import subprocess
import os
from datetime import datetime
from pathlib import Path

import streamlit as st


def _unc_to_local(p: str) -> str:
    """Convert \\\\hostname\\e$\\foo\\bar to E:\\foo\\bar"""
    if p.startswith('\\\\'):
        try:
            parts = p.lstrip('\\').split('\\')
            if len(parts) >= 2:
                drive = parts[1][0].upper() + ':'
                rest = parts[2:]
                return os.path.join(drive + '\\', *rest) if rest else drive + '\\'
        except Exception:
            pass
    return p


def _host_from_unc(p: str) -> str:
    """Extract hostname from \\\\hostname\\share"""
    try:
        return p.lstrip('\\').split('\\')[0]
    except Exception:
        return ""


def render_tab10() -> None:
    st.subheader("Service Restarts")
    st.info(
        "This will execute the restart script **remotely** on the upper server via scheduled task."
    )

    site_name = (st.session_state.get("site_name") or "").strip()
    upper_base = (st.session_state.get("upper_base_path") or "").strip()

    if not site_name:
        st.warning("Please set the site name in Setup Steps (Tab 1) before running the restart script.")
        return

    if not upper_base:
        st.warning("Please select the upper server in Setup Steps (Tab 1).")
        return

    upper_hostname = _host_from_unc(upper_base)
    if not upper_hostname:
        st.error("Could not determine upper server hostname from path.")
        return

    # Build paths: UNC for existence check, local for remote execution
    unc_script_dir = os.path.join(upper_base, "Applied Materials", "SFRxServiceRestarts")
    unc_script_path = os.path.join(unc_script_dir, f"{site_name}ServiceRestart.bat")
    local_script_path = _unc_to_local(unc_script_path)

    st.markdown("**Restart script**")
    st.caption(f"Upper server: `{upper_hostname}`")
    st.caption(f"Remote path: `{local_script_path}`")
    st.caption(f"UNC path: `{unc_script_path}`")

    test_mode = st.checkbox(
        "🧪 Test Mode (do not execute, just simulate)",
        value=False,
        key="restart_services_test_mode",
    )

    # Credentials for schtasks authentication to remote server
    st.markdown("---")
    st.markdown("**Credentials** (for scheduled task on upper server)")
    col_user, col_pass = st.columns(2)
    with col_user:
        username = st.text_input("Username", key="restart_username", placeholder="A-USERNAME")
    with col_pass:
        password = st.text_input("Password", key="restart_password", type="password")

    def _run_restart_script():
        # Check file exists via UNC path
        if not Path(unc_script_path).exists():
            st.error(f"Script not found via UNC: `{unc_script_path}`")
            st.info("Make sure the upper server's E$ share is accessible from this machine.")
            return

        if test_mode:
            st.success(f"[TEST MODE] Would execute remotely on `{upper_hostname}`:")
            st.code(local_script_path, language="batch")
            return

        if not username or not password:
            st.error("Username and password are required to create a scheduled task on the remote server.")
            return

        task_name = f"SFRx_{site_name}_ServiceRestart_{datetime.now().strftime('%H%M%S')}"

        with st.spinner(f"Running restart script on {upper_hostname}..."):
            try:
                # Use PowerShell CIM session with DCOM protocol so credentials
                # stay in-memory (piped via stdin) and never appear in process
                # command-line arguments visible to EDR / security tooling.
                safe_user = username.replace("'", "''")
                safe_pass = password.replace("'", "''")
                safe_host = upper_hostname.replace("'", "''")
                safe_task = task_name.replace("'", "''")
                safe_script = local_script_path.replace("'", "''")

                ps_script = f"""
$ErrorActionPreference = 'Stop'
try {{
    # Build credential in memory - never on command line
    $pass = ConvertTo-SecureString '{safe_pass}' -AsPlainText -Force
    $cred = [PSCredential]::new('{safe_user}', $pass)

    # Connect via DCOM (RPC port 135) - works even when WinRM is blocked
    $opt  = New-CimSessionOption -Protocol Dcom
    $sess = New-CimSession -ComputerName '{safe_host}' -Credential $cred -SessionOption $opt
    Write-Output 'CIM session established'

    # Create scheduled task
    $action    = New-ScheduledTaskAction -Execute 'cmd' -Argument '/c ""{safe_script}""'
    $principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
    Register-ScheduledTask -TaskName '{safe_task}' -Action $action -Principal $principal -CimSession $sess -Force | Out-Null
    Write-Output 'Task created: {safe_task}'

    # Run immediately
    Start-ScheduledTask -TaskName '{safe_task}' -CimSession $sess
    Write-Output 'Task started'

    # Wait and check status
    Start-Sleep -Seconds 10
    $info = Get-ScheduledTaskInfo -TaskName '{safe_task}' -CimSession $sess
    Write-Output "Last run result: $($info.LastTaskResult)"
    Write-Output "Last run time:   $($info.LastRunTime)"

    # Clean up
    Unregister-ScheduledTask -TaskName '{safe_task}' -CimSession $sess -Confirm:$false
    Write-Output 'Task cleaned up'

    Remove-CimSession -CimSession $sess
    Write-Output 'DONE'
}} catch {{
    Write-Error $_.Exception.Message
    exit 1
}}
"""

                st.text("Connecting to remote server via CIM/DCOM...")

                # Credentials are piped via stdin - command line only shows
                # "powershell.exe -NoProfile -Command -"
                process = subprocess.Popen(
                    ['powershell.exe', '-NoProfile', '-Command', '-'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = process.communicate(
                    input=ps_script, timeout=120
                )

                if stdout:
                    for line in stdout.strip().splitlines():
                        if line.startswith("Task created"):
                            st.text(f"✓ {line}")
                        elif line.startswith("Task started"):
                            st.text(f"✓ {line}")
                        elif line.startswith("Task cleaned"):
                            st.text(f"✓ {line}")
                        elif line == "DONE":
                            pass
                        else:
                            st.text(line)

                if process.returncode == 0:
                    st.success(f"✅ Restart script executed on {upper_hostname}")
                else:
                    err_msg = stderr.strip() if stderr else stdout
                    st.error(f"❌ Failed (exit {process.returncode}): {err_msg}")

            except subprocess.TimeoutExpired:
                process.kill()
                st.error("Operation timed out after 120 seconds")
            except Exception as exc:
                st.error(f"Error: {exc}")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶️ Run Restart Script", type="primary", use_container_width=True):
            _run_restart_script()
