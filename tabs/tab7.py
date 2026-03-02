import streamlit as st
import os
import subprocess
from datetime import datetime, timedelta


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


def render_tab7() -> None:
    st.subheader("Portal Dashboard Migration - CLI Import")

    site_name = st.session_state.get("site_name", "")
    upper_base = st.session_state.get("upper_base_path", "").strip()
    base_for_display = upper_base if upper_base else r"\\<upper-server>\e$"

    if site_name:
        cli_path = f"{base_for_display}\\Applied Materials\\SmartFactoryRx_{site_name}\\CLI\\bin"
    else:
        cli_path = f"{base_for_display}\\Applied Materials\\SmartFactoryRx_<Site>\\CLI\\bin"

    st.markdown(
        f"""
        ### Instructions
        These commands must be run manually on the **upper server**.

        1. Click **Generate Commands** to create the CLI import commands.
        2. Review the generated commands below.
        3. RDP into the upper server and open a **Command Prompt**.
        4. Navigate to the CLI directory:
           ```
           cd "{_unc_to_local(cli_path)}"
           ```
        5. Copy and paste each command one at a time. Your **username and password** will be prompted by the CLI.
        """
    )

    def _get_base_path() -> str:
        upper_base_val = st.session_state.get("upper_base_path", "").strip()
        return upper_base_val.rstrip("\\/") if upper_base_val else ""

    if st.button("Generate Commands", key="generate_cli_import_commands"):
        site_name = st.session_state.get("site_name", "")
        release_name = st.session_state.get("release_name", "")
        equipments_file = st.session_state.get("equipments_file")
        equipments_text = st.session_state.get("equipments_text", "")

        if not site_name:
            st.error("Please enter the site name in Setup Steps (Tab 1)")
        elif not release_name:
            st.error("Please enter the release name in Setup Steps (Tab 1)")
        elif not _get_base_path():
            st.error("Please select the upper server in Setup Steps (Tab 1)")
        elif not equipments_file and not equipments_text:
            st.error("Please upload the equipments file or enter equipment names in Setup Steps (Tab 1)")
        else:
            try:
                base_path = _get_base_path()
                migration_folder_path = os.path.join(
                    base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "Migration", release_name
                )
                commands = generate_cli_import_commands(site_name, release_name, migration_folder_path, equipments_file, equipments_text)
                st.session_state['cli_import_commands'] = commands
            except Exception as e:
                st.error(f"Error generating commands: {str(e)}")

    if 'cli_import_commands' in st.session_state and st.session_state['cli_import_commands']:
        st.text_area(
            "Generated Commands:",
            value=st.session_state['cli_import_commands'],
            height=300,
            disabled=True,
            key="cli_import_commands_display"
        )

        st.info("Copy the commands above and paste them one by one in the CLI on the upper server.")

        # --- Automated execution disabled (sfrxcli hangs with stdin redirect) ---
        # TODO: Re-enable once a reliable remote execution method is confirmed.
        # test_mode = st.checkbox("Test Mode (simulate CLI execution without sfrxcli)", value=False, key="cli_import_test_mode")
        # if test_mode:
        #     st.info("Test mode enabled - will simulate CLI execution for testing purposes")
        #
        # col1, col2, col3 = st.columns([1, 2, 1])
        # with col2:
        #     if st.button("Run CLI Import Commands", type="primary", use_container_width=True):
        #         try:
        #             site_name = st.session_state.get("site_name", "")
        #             release_name = st.session_state.get("release_name", "")
        #             equipments_file = st.session_state.get("equipments_file")
        #             equipments_text = st.session_state.get("equipments_text", "")
        #             test_mode = st.session_state.get("cli_import_test_mode", False)
        #
        #             base_path = _get_base_path()
        #             if not base_path:
        #                 st.error("Please select the upper server in Setup Steps (Tab 1)")
        #                 st.stop()
        #
        #             migration_folder_path = os.path.join(
        #                 base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "Migration", release_name
        #             )
        #
        #             with st.spinner("Running CLI import commands..." if not test_mode else "Simulating CLI import commands..."):
        #                 result = run_cli_import_commands(
        #                     site_name, release_name, migration_folder_path,
        #                     equipments_file, equipments_text, test_mode
        #                 )
        #
        #             if result["success"]:
        #                 st.success("Commands executed successfully!")
        #                 st.caption(f"Log file: {result['log_file']}")
        #             else:
        #                 st.error(f"Error: {result['error']}")
        #
        #             if result["output"]:
        #                 st.markdown("### Command Output")
        #                 st.code(result["output"], language="text")
        #
        #         except Exception as e:
        #             st.error(f"Error running commands: {str(e)}")


def generate_cli_import_commands(site_name: str, release_name: str, migration_folder_path: str, equipments_file, equipments_text: str) -> str:
    """Generate CLI import commands preview (mirrors tab3 generate_cli_commands)."""
    if equipments_file:
        equipments_file.seek(0)
        content = equipments_file.read().decode('utf-8')
        equipments = [l.strip() for l in content.splitlines() if l.strip()]
    else:
        equipments = [l.strip() for l in equipments_text.splitlines() if l.strip()]

    upper_base = st.session_state.get("upper_base_path", "").strip().rstrip("\\")
    cli_bin_unc = os.path.join(upper_base, "Applied Materials", f"SmartFactoryRx_{site_name}", "CLI", "bin")
    cli_bin_local = _unc_to_local(cli_bin_unc)
    remote_exe = os.path.join(cli_bin_local, "sfrxcli.exe")
    remote_host = _host_from_unc(upper_base) or "<upper-server>"
    migration_local = _unc_to_local(migration_folder_path)

    lines = [f"# Runs on: {remote_host} via Invoke-Command", f"cd '{cli_bin_local}'", ""]
    for equipment in equipments:
        json_local = os.path.join(migration_local, f"{release_name}-{equipment}.json")
        csv_local  = os.path.join(migration_local, f"{release_name}-{equipment}.csv")
        lines.append(f"& '{remote_exe}' ie -if '{json_local}' --comment '{release_name}' --env {site_name}")
        lines.append(f"& '{remote_exe}' is -if '{csv_local}' --comment '{release_name}' --env {site_name}")
        lines.append("")
    return "\n".join(lines)


def run_cli_import_commands(site_name: str, release_name: str, migration_folder_path: str, equipments_file, equipments_text: str, test_mode: bool = False) -> dict:
    """Run CLI import commands on the upper server via schtasks (no WinRM required)."""
    import time

    log_file_path = "N/A"
    log_lines = []
    full_output = ""

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = os.path.join(migration_folder_path, f"{release_name}_cli_import_log_{timestamp}.log")

        if equipments_file:
            equipments_file.seek(0)
            content = equipments_file.read().decode('utf-8')
            equipments = [l.strip() for l in content.splitlines() if l.strip()]
        else:
            equipments = [l.strip() for l in equipments_text.splitlines() if l.strip()]

        upper_base = st.session_state.get("upper_base_path", "").strip().rstrip("\\")
        migration_local = _unc_to_local(migration_folder_path)
        remote_host = _host_from_unc(upper_base)
        remote_username = st.session_state.get("remote_username", "").strip()
        remote_password = st.session_state.get("remote_password", "")

        cli_bin_unc = os.path.join(upper_base, "Applied Materials", f"SmartFactoryRx_{site_name}", "CLI", "bin")
        cli_bin_local = _unc_to_local(cli_bin_unc)
        exe_local = os.path.join(cli_bin_local, "sfrxcli.exe")

        log_lines = [
            "=== CLI Import Commands Execution Log ===",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Site: {site_name}",
            f"Release: {release_name}",
            f"Mode: {'TEST (Simulated)' if test_mode else 'PRODUCTION'}",
            "=" * 50,
        ]

        if test_mode:
            cmds_preview = []
            for equipment in equipments:
                json_f = os.path.join(migration_local, f"{release_name}-{equipment}.json")
                csv_f  = os.path.join(migration_local, f"{release_name}-{equipment}.csv")
                cmds_preview += [f'ie -if "{json_f}" --comment "{release_name}"',
                                  f'is -if "{csv_f}" --comment "{release_name}"']
            log_lines.append("\n[TEST MODE] Commands:\n" + "\n".join(cmds_preview) + "\n")
            simulated = [
                "SmartFactoryRx CLI v2.5.1",
                f"Connecting to environment: {site_name}...",
                "Connected successfully.", "",
            ]
            for equipment in equipments:
                simulated += [f"Importing: {equipment}",
                               f"  ie ({release_name}-{equipment}.json) ... Done",
                               f"  is ({release_name}-{equipment}.csv) ... Done", ""]
            simulated.append("All imports completed successfully!")
            full_output = "\n".join(simulated)
            log_lines += [full_output, f"\n{'=' * 50}", "[TEST MODE] Simulated exit code: 0",
                          f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_lines))
            return {"success": True, "output": full_output, "error": None, "log_file": log_file_path}

        if not upper_base:
            return {"success": False, "output": "", "error": "Upper server base path required in Setup (Tab 1)", "log_file": log_file_path}
        if not remote_host:
            raise RuntimeError("Could not determine remote host from upper base path")
        if not remote_username or not remote_password:
            return {"success": False, "output": "", "error": "Remote credentials required in Setup (Tab 1)", "log_file": log_file_path}

        def _ps_sq(s):
            return s.replace("'", "''")

        # Build sfrxcli stdin commands (no --env needed in interactive mode)
        cmds_for_stdin = []
        for equipment in equipments:
            json_file = os.path.join(migration_local, f"{release_name}-{equipment}.json")
            csv_file  = os.path.join(migration_local, f"{release_name}-{equipment}.csv")
            cmds_for_stdin.append(f'ie -if "{json_file}" --comment "{release_name}"')
            cmds_for_stdin.append(f'is -if "{csv_file}" --comment "{release_name}"')
        cmds_for_stdin.append('exit')

        # Temp file paths: UNC for app server to write/read, local for the PS1 script running on server
        output_local = os.path.join(migration_local, f"cli_import_output_{timestamp}.txt")
        output_unc   = os.path.join(migration_folder_path, f"cli_import_output_{timestamp}.txt")
        script_local = os.path.join(migration_local, f"run_import_{timestamp}.ps1")
        script_unc   = os.path.join(migration_folder_path, f"run_import_{timestamp}.ps1")

        # Build PS1 script that pipes stdin to sfrxcli
        ps1_lines = [
            f"$exe = '{_ps_sq(exe_local)}'",
            f"$dir = '{_ps_sq(cli_bin_local)}'",
            f"$outFile = '{_ps_sq(output_local)}'",
            "try {",
            "    $p = New-Object System.Diagnostics.Process",
            "    $p.StartInfo.FileName = $exe",
            f"    $p.StartInfo.Arguments = '-i --env {site_name}'",
            "    $p.StartInfo.WorkingDirectory = $dir",
            "    $p.StartInfo.UseShellExecute = $false",
            "    $p.StartInfo.RedirectStandardInput = $true",
            "    $p.StartInfo.RedirectStandardOutput = $true",
            "    $p.StartInfo.RedirectStandardError = $true",
            "    $p.Start() | Out-Null",
            f"    $p.StandardInput.WriteLine('{_ps_sq(remote_username)}')",
            f"    $p.StandardInput.WriteLine('{_ps_sq(remote_password)}')",
        ]
        for cmd in cmds_for_stdin:
            ps1_lines.append(f"    $p.StandardInput.WriteLine('{_ps_sq(cmd)}')"
        )
        ps1_lines += [
            "    $p.StandardInput.Close()",
            "    $out = $p.StandardOutput.ReadToEnd()",
            "    $err = $p.StandardError.ReadToEnd()",
            "    $p.WaitForExit()",
            '    ($out + "`n" + $err) | Out-File -FilePath $outFile -Encoding UTF8',
            "} catch {",
            '    "ERROR: $_" | Out-File -FilePath $outFile -Encoding UTF8',
            "}",
        ]
        ps1_content = "\r\n".join(ps1_lines) + "\r\n"

        # Write PS1 to server via UNC
        with open(script_unc, 'w', encoding='utf-8') as f:
            f.write(ps1_content)

        task_name = f"SFRxImport_{timestamp}"
        tr = f'powershell -NoProfile -ExecutionPolicy Bypass -File "{script_local}"'

        # Establish IPC$ connection to remote host (avoids "logon session" errors)
        ipc_r = subprocess.run(
            ["net", "use", f"\\\\{remote_host}\\IPC$",
             f"/user:{remote_username}", remote_password],
            capture_output=True, text=True, timeout=30
        )
        # IPC$ may already be connected — ignore "duplicate" errors
        if ipc_r.returncode != 0 and "1219" not in ipc_r.stderr and "1219" not in ipc_r.stdout:
            log_lines.append(f"IPC$ warning: {ipc_r.stdout.strip()} {ipc_r.stderr.strip()}")

        # Use a start time 2 minutes in the future (schtasks rejects past times)
        future_st = (datetime.now() + timedelta(minutes=2)).strftime("%H:%M")

        # Create remote scheduled task (run as SYSTEM to avoid logon session errors)
        create_r = subprocess.run(
            ["schtasks", "/create", "/s", remote_host,
             "/u", remote_username, "/p", remote_password,
             "/tn", task_name, "/tr", tr,
             "/sc", "ONCE", "/st", future_st,
             "/ru", "SYSTEM", "/f"],
            capture_output=True, text=True, timeout=30
        )
        if create_r.returncode != 0:
            raise RuntimeError(f"schtasks /create failed: {create_r.stdout.strip()} {create_r.stderr.strip()}")

        # Run immediately
        run_r = subprocess.run(
            ["schtasks", "/run", "/s", remote_host,
             "/u", remote_username, "/p", remote_password,
             "/tn", task_name],
            capture_output=True, text=True, timeout=30
        )
        if run_r.returncode != 0:
            raise RuntimeError(f"schtasks /run failed: {run_r.stdout.strip()} {run_r.stderr.strip()}")

        log_lines.append(f"\nTask '{task_name}' started on {remote_host}. Waiting for completion...\n")

        # Poll until task is no longer Running (up to 10 min)
        for _ in range(120):
            time.sleep(5)
            q = subprocess.run(
                ["schtasks", "/query", "/s", remote_host,
                 "/u", remote_username, "/p", remote_password,
                 "/tn", task_name, "/fo", "LIST"],
                capture_output=True, text=True, timeout=30
            )
            if "Running" not in q.stdout:
                break

        # Read output via UNC
        if os.path.exists(output_unc):
            with open(output_unc, 'r', encoding='utf-8', errors='replace') as f:
                full_output = f.read()
        else:
            full_output = "[No output file found - task may have failed to start]"

        # Clean up task and temp files
        subprocess.run(
            ["schtasks", "/delete", "/s", remote_host,
             "/u", remote_username, "/p", remote_password,
             "/tn", task_name, "/f"],
            capture_output=True, text=True, timeout=30
        )
        for tmp in [script_unc, output_unc]:
            try:
                os.remove(tmp)
            except Exception:
                pass

        log_lines += [full_output, f"\n{'=' * 50}",
                      f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_lines))

        success = bool(full_output.strip()) and not full_output.strip().startswith("ERROR")
        return {"success": success, "output": full_output,
                "error": None if success else "Check output for errors",
                "log_file": log_file_path}

    except Exception as e:
        error_msg = str(e)
        log_lines.append(f"\n\nEXCEPTION: {error_msg}")
        try:
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_lines))
        except Exception:
            pass
        return {"success": False, "output": '\n'.join(log_lines), "error": error_msg, "log_file": log_file_path}