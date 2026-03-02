# Copilot Instructions - Migration Automation

## Project Overview

**SmartFactory Rx Migration Automation Tool** — a Streamlit web app that automates equipment configuration migration between SmartFactory Rx environments (QA → Production). Deployed on a Windows server in the same network as the target upper/lower servers.

- **Branch**: `poc-unc-support` (active development)
- **Repo**: `juandaslalom/migration_automation`
- **Framework**: Streamlit + Python 3.12
- **Auth**: `streamlit-authenticator` (v0.4.x) with credentials in `.streamlit/secrets.toml`

## Architecture

### File Structure

```
migration_automation/
├── app.py                  # Main entry, auth, tab routing (10 tabs)
├── tabs/
│   ├── tab1.py             # Setup Steps (site, release, drive, equipments, credentials)
│   ├── tab2.py             # E3 Export
│   ├── tab3.py             # CLI Export (lower server, Invoke-Command + PSCredential)
│   ├── tab4.py             # Folder Migration (UNC copy via net use + shutil)
│   ├── tab5.py             # Import Files (upper server paths)
│   ├── tab6.py             # E3 Import (remote service restart via sc + IPC$)
│   ├── tab7.py             # CLI Import (upper server, schtasks + stdin piping)
│   ├── tab8.py             # Dashboard CLI Import (upper server, schtasks + stdin piping)
│   ├── tab9.py             # Guardbands Import (info-only, no buttons)
│   └── tab10.py            # Service Restarts (bat file runner)
├── CLAUDE.md               # Original project context doc
├── IMPLEMENTATION.md        # Implementation notes
├── requirements.txt
├── dev_session_state.json   # Dev tool state persistence
├── example_equipments.txt
├── nginx.conf
├── run_poc.ps1
└── setup_*.ps1
```

### Session State Keys (set in Tab 1)

| Key | Description |
|-----|-------------|
| `site_name` | Target site (e.g., "Westport") |
| `release_name` | Release identifier (e.g., "20260225-TestDummyMigration") |
| `base_drive` | Drive letter (e.g., "E:") |
| `lower_base_path` | UNC to lower server (e.g., `\\10.72.100.15\E$`) |
| `upper_base_path` | UNC to upper server (e.g., `\\WA01928Q\E$`) |
| `remote_username` | Credentials for remote execution (e.g., "A-DAVIDJX8") |
| `remote_password` | Password for remote execution |
| `equipments_file` | Uploaded equipment list file |
| `equipments_text` | Manual equipment names (textarea) |

### Helper Functions (shared across tabs)

```python
def _unc_to_local(p: str) -> str:
    """Convert \\\\hostname\\e$\\foo\\bar -> E:\\foo\\bar"""

def _host_from_unc(p: str) -> str:
    """Extract hostname from \\\\hostname\\share"""
```

## Remote Execution Patterns

### CRITICAL: sfrxcli 1.7.4 Limitations

- **sfrxcli does NOT support `--user`/`--password` flags** — credentials can ONLY be provided via stdin
- **sfrxcli prompts interactively** for username then password
- **WinRM (Invoke-Command) is blocked** between the app server and upper server WA01928Q
- **schtasks works** between the app server and upper server (RPC port 135 is open)

### Pattern 1: Invoke-Command (Tab 3 - Lower Server)

Used for CLI Export on the lower server where WinRM IS available. Non-interactive commands (sfrxcli auto-authenticates without user/pass prompts):

```python
# Build per-command invocations
invocations = [f"& '{sfrxcli_path}' {cmd} --env {site}" for cmd in commands]
remote_script = f"cd '{cli_bin}'; {'; '.join(invocations)}"

# PSCredential for Invoke-Command auth (NOT sfrxcli auth)
cred_setup = "$pass = ConvertTo-SecureString '...' -AsPlainText -Force; $cred = New-Object PSCredential('...', $pass); "
ps_cmd = f"{cred_setup}Invoke-Command -ComputerName {host} -Credential $cred -ScriptBlock {{ {remote_script} }}"
subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd], timeout=900)
```

### Pattern 2: schtasks + stdin piping (Tab 7 & Tab 8 - Upper Server)

Used for CLI Import and Dashboard Import where WinRM is blocked. Creates a PS1 script that pipes stdin to sfrxcli, deploys via UNC, runs via schtasks:

```python
# 1. Build PS1 script using System.Diagnostics.Process to pipe stdin
ps1_lines = [
    "$p = New-Object System.Diagnostics.Process",
    "$p.StartInfo.FileName = $exe",
    "$p.StartInfo.Arguments = '-i --env SITE'",
    "$p.StartInfo.RedirectStandardInput = $true",
    "$p.StartInfo.RedirectStandardOutput = $true",
    "$p.Start() | Out-Null",
    "$p.StandardInput.WriteLine('USERNAME')",
    "$p.StandardInput.WriteLine('PASSWORD')",
    "$p.StandardInput.WriteLine('ie -if \"file.json\" --comment \"release\"')",
    "$p.StandardInput.WriteLine('exit')",
    "$p.StandardInput.Close()",
    "$out = $p.StandardOutput.ReadToEnd()",
    "$p.WaitForExit()",
    "$out | Out-File -FilePath $outFile -Encoding UTF8",
]

# 2. Write PS1 to server via UNC path
with open(script_unc, 'w') as f: f.write(ps1_content)

# 3. Create + run scheduled task
subprocess.run(["schtasks", "/create", "/s", host, "/u", user, "/p", pw,
                "/tn", task_name, "/tr", f'powershell -File "{script_local}"',
                "/sc", "ONCE", "/st", "00:00", "/ru", user, "/rp", pw, "/f"])
subprocess.run(["schtasks", "/run", "/s", host, "/u", user, "/p", pw, "/tn", task_name])

# 4. Poll until done, read output via UNC, clean up
```

### Pattern 3: sc + IPC$ (Tab 6 - Service Restart)

Service restarts use `sc \\hostname stop/start ServiceName` with IPC$ authentication.

### Pattern 4: UNC + shutil (Tab 4 - File Copy)

Folder migration uses `net use` to map UNC paths then `shutil.copytree` / `shutil.copy2`.

## CLI Commands Reference

### Export (Tab 3 - lower server, non-interactive)
```
sfrxcli.exe ee -of "{path}\{release}-{equip}.json" -en {equip} --env {site}
sfrxcli.exe es -of "{path}\{release}-{equip}.csv" -en {equip} --env {site}
```

### Import (Tab 7 - upper server, interactive via stdin)
```
ie -if "{path}\{release}-{equip}.json" --comment "{release}"
is -if "{path}\{release}-{equip}.csv" --comment "{release}"
exit
```

### Dashboard Import (Tab 8 - upper server, interactive via stdin)
```
ds --import --setting-type ProcessMap --static-file-directory "{static_path}"
ds --import --setting-type EquipmentHealth --static-file-directory "{static_path}"
ds --import --setting-type EquipmentView --static-file-directory "{static_path}"
ds --import --setting-type Operation --static-file-directory "{static_path}"
exit
```

## Server Topology

```
[App Server] ──UNC──> [Lower Server (QA)]     e.g., \\10.72.100.15\E$
     │                  └─ WinRM works (Invoke-Command OK)
     │
     └────UNC+RPC───> [Upper Server (Prod)]    e.g., \\WA01928Q\E$
                       └─ WinRM BLOCKED (use schtasks instead)
                       └─ schtasks works (RPC port 135 open)
                       └─ sc works (service control)
                       └─ net use works (file access)
```

## Directory Paths on Servers

```
E:\Applied Materials\SmartFactoryRx_{site}\
├── CLI\bin\sfrxcli.exe
├── Migration\{release}\
│   ├── {release}-{equipment}.json
│   └── {release}-{equipment}.csv
├── Portal\data\static\
│   ├── ProcessMap\
│   ├── Equipment\
│   ├── Operation\
│   └── dmx\
└── Guardbands\
```

## Recent Implementation History (poc-unc-support branch)

| Commit | Change |
|--------|--------|
| `8d798f3` | Tab7+Tab8: schtasks approach — writes PS1 via UNC, creates remote schtask, pipes stdin to sfrxcli, polls completion, reads output back |
| `490328d` | Tab7+Tab8: clean UTF-8 rewrite with Invoke-Command pattern (replaced by schtasks) |
| `263f0af` | Tab7+Tab8: wmic + net use approach (replaced by Invoke-Command, then schtasks) |
| `c39df50` | Added Tab9 (Guardbands info) and Tab10 (Service Restarts, renamed from old Tab9) |
| `4a38782` | Fixed Unicode corruption across tab7/tab8 |
| Earlier | Tab1-Tab6 all working: Tab3 Invoke-Command export, Tab4 UNC shutil copy, Tab6 sc service restart |

## Known Issues

1. **`app.py` line 166**: `render_tab10()` is called twice (duplicate `with tab10:` block) — should remove the last 2 lines
2. **Tab7/Tab8 not yet tested end-to-end** via the Streamlit UI with schtasks approach — was verified that `schtasks /query` reaches WA01928Q successfully
3. **sfrxcli interactive mode** requires username + password as first two stdin lines, then commands, then `exit`
4. **Tab 3 (CLI Export)** uses Invoke-Command which works for the lower server but would NOT work for the upper server

## Next Steps / TODO

### Immediate Testing
- [ ] Test Tab 7 (CLI Import) end-to-end through Streamlit UI on the app server
- [ ] Test Tab 8 (Dashboard CLI Import) end-to-end through Streamlit UI
- [ ] Verify schtasks cleanup (task deleted, temp files removed)
- [ ] Verify output file is correctly read back and displayed

### Bug Fixes
- [ ] Remove duplicate `render_tab10()` in `app.py` (line 165-166)
- [ ] Tab 7/8: Add progress indicator showing schtask polling status (currently just a spinner)

### Enhancements
- [ ] Add timeout handling for schtask polling (currently 10 min max, exits silently)
- [ ] Add validation that .json/.csv files exist on server before running import
- [ ] Add file count/summary before running import commands
- [ ] Consider adding a "dry run" mode that shows exactly what schtasks commands will execute
- [ ] Implement rollback functionality
- [ ] Export/import configuration profiles
- [ ] Tab 9 (Guardbands): May need actual import functionality added later

### Infrastructure
- [ ] Test deployment on actual app server (not developer laptop)
- [ ] Verify nginx reverse proxy config works with authentication
- [ ] Consider adding HTTPS/TLS

## Development Conventions

- Each tab is a separate file `tabs/tabN.py` with a `render_tabN()` function
- All CLI operations support test mode (simulate without sfrxcli)
- Log files written with timestamp: `{operation}_log_{YYYYMMDD_HHMMSS}.log`
- UNC paths used for cross-server file access; `_unc_to_local()` converts for server-local execution
- Credentials never persisted to disk — session-only via `st.session_state`
- Use `subprocess.run()` for one-shot commands, `subprocess.Popen()` only when stdin piping is needed locally

## Running the App

```powershell
# Development
.\venv\Scripts\Activate.ps1
streamlit run app.py

# Production
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```
