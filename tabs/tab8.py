import streamlit as st
import os
import subprocess
import time
from datetime import datetime


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


def render_tab8() -> None:
    st.subheader("Dashboard CLI Import")

    site_name = st.session_state.get("site_name", "")
    upper_base = st.session_state.get("upper_base_path", "").strip()
    base_for_display = upper_base if upper_base else r"\\<upper-server>\e$"

    if site_name:
        cli_path = f"{base_for_display}\\Applied Materials\\SmartFactoryRx_{site_name}\\CLI\\bin"
        static_path = f"{base_for_display}\\Applied Materials\\SmartFactoryRx_{site_name}\\Portal\\data\\static"
    else:
        cli_path   = f"{base_for_display}\\Applied Materials\\SmartFactoryRx_<Site>\\CLI\\bin"
        static_path = f"{base_for_display}\\Applied Materials\\SmartFactoryRx_<Site>\\Portal\\data\\static"

    st.markdown(
        f"""
        ### Instructions
        Imports dashboard domain settings (ProcessMap, EquipmentHealth, EquipmentView, Operation).

        - CLI bin directory: `{cli_path}`
        - Static files directory: `{static_path}`

        1. Click **Generate Dashboard Commands** to preview the import commands.
        2. Click **Run Dashboard CLI Import** to execute them on the upper server.
        """
    )

    def _get_base_path() -> str:
        v = st.session_state.get("upper_base_path", "").strip()
        return v.rstrip("\\/") if v else ""

    if st.button("Generate Dashboard Commands", key="generate_dashboard_cli_commands"):
        site_name = st.session_state.get("site_name", "")
        if not site_name:
            st.error("Please enter the site name in Setup Steps (Tab 1)")
        elif not _get_base_path():
            st.error("Please select the upper server in Setup Steps (Tab 1)")
        else:
            try:
                base_path = _get_base_path()
                static_unc = os.path.join(base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "Portal", "data", "static")
                commands = generate_dashboard_commands(site_name, static_unc)
                st.session_state['dashboard_cli_commands'] = commands
            except Exception as e:
                st.error(f"Error generating commands: {str(e)}")

    if 'dashboard_cli_commands' in st.session_state and st.session_state['dashboard_cli_commands']:
        st.text_area(
            "Generated Dashboard Commands:",
            value=st.session_state['dashboard_cli_commands'],
            height=200,
            disabled=True,
            key="dashboard_cli_commands_display"
        )

        st.markdown("---")

        test_mode = st.checkbox("Test Mode (simulate CLI execution without sfrxcli)", value=False, key="dashboard_cli_test_mode")
        if test_mode:
            st.info("Test mode enabled - will simulate CLI execution")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Run Dashboard CLI Import", type="primary", use_container_width=True):
                try:
                    site_name = st.session_state.get("site_name", "")
                    test_mode = st.session_state.get("dashboard_cli_test_mode", False)
                    base_path = _get_base_path()
                    if not base_path:
                        st.error("Please select the upper server in Setup Steps (Tab 1)")
                        st.stop()

                    static_unc = os.path.join(base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "Portal", "data", "static")
                    log_folder = os.path.join(base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "Migration")

                    with st.spinner("Running dashboard CLI import..." if not test_mode else "Simulating dashboard CLI import..."):
                        result = run_dashboard_cli_commands(site_name, static_unc, log_folder, test_mode)

                    if result["success"]:
                        st.success("Dashboard import completed successfully!")
                        st.caption(f"Log file: {result['log_file']}")
                    else:
                        st.error(f"Error: {result['error']}")

                    if result["output"]:
                        st.markdown("### Command Output")
                        st.code(result["output"], language="text")

                except Exception as e:
                    st.error(f"Error running dashboard import: {str(e)}")


def generate_dashboard_commands(site_name: str, static_unc: str) -> str:
    """Generate DS import command preview."""
    upper_base = st.session_state.get("upper_base_path", "").strip().rstrip("\\")
    cli_bin_unc   = os.path.join(upper_base, "Applied Materials", f"SmartFactoryRx_{site_name}", "CLI", "bin")
    cli_bin_local = _unc_to_local(cli_bin_unc)
    remote_exe    = os.path.join(cli_bin_local, "sfrxcli.exe")
    remote_host   = _host_from_unc(upper_base) or "<upper-server>"
    static_local  = _unc_to_local(static_unc)

    setting_types = ["ProcessMap", "EquipmentHealth", "EquipmentView", "Operation"]
    lines = [f"# Runs on: {remote_host} via Invoke-Command", f"cd '{cli_bin_local}'", ""]
    for st_type in setting_types:
        lines.append(f"& '{remote_exe}' ds --import --setting-type {st_type} --static-file-directory \"{static_local}\" --env {site_name}")
    return "\n".join(lines)


def run_dashboard_cli_commands(site_name: str, static_unc: str, log_folder: str, test_mode: bool = False) -> dict:
    """Run DS import commands on the upper server (mirrors tab3 run_cli_commands)."""

    log_file_path = None
    log_lines = []
    full_output = ""

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = os.path.join(log_folder, f"dashboard_cli_import_log_{timestamp}.log")

        upper_base    = st.session_state.get("upper_base_path", "").strip().rstrip("\\")
        cli_bin_unc   = os.path.join(upper_base, "Applied Materials", f"SmartFactoryRx_{site_name}", "CLI", "bin")
        cli_bin_local = _unc_to_local(cli_bin_unc)
        remote_exe    = os.path.join(cli_bin_local, "sfrxcli.exe")
        remote_host   = _host_from_unc(upper_base)
        static_local  = _unc_to_local(static_unc)

        setting_types = ["ProcessMap", "EquipmentHealth", "EquipmentView", "Operation"]

        log_lines = [
            "=== Dashboard CLI Import Execution Log ===",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Site: {site_name}",
            f"Static files dir: {static_local}",
            f"Mode: {'TEST (Simulated)' if test_mode else 'PRODUCTION'}",
            "=" * 50,
        ]

        if test_mode:
            lines = []
            for st_type in setting_types:
                lines.append(f"ds --import --setting-type {st_type} --static-file-directory \"{static_local}\"")
            log_lines.append(f"\n[TEST MODE] Commands:\n" + "\n".join(lines) + "\n")
            simulated = [
                "SmartFactoryRx CLI v2.5.1",
                f"Connecting to environment: {site_name}...",
                f"Connected successfully.",
                "",
            ]
            for st_type in setting_types:
                simulated.append(f"Importing {st_type} from {static_local}...")
                simulated.append(f"  {st_type} import ... Done")
                simulated.append("")
            simulated.append("All dashboard imports completed successfully!")
            full_output = "\n".join(simulated)
            log_lines.append(full_output)
            log_lines.append(f"\n{'=' * 50}")
            log_lines.append("[TEST MODE] Simulated exit code: 0")
            log_lines.append(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_lines))
            return {"success": True, "output": full_output, "error": None, "log_file": log_file_path}

        if not upper_base:
            return {"success": False, "output": "", "error": "Upper server base path required in Setup (Tab 1)", "log_file": log_file_path}
        if not remote_host:
            raise RuntimeError("Could not determine remote host from upper base path")

        remote_username = st.session_state.get("remote_username", "").strip()
        remote_password = st.session_state.get("remote_password", "")
        if not remote_username or not remote_password:
            return {"success": False, "output": "", "error": "Remote credentials required in Setup (Tab 1)", "log_file": log_file_path}

        def _ps_sq(s):
            return s.replace("'", "''")

        # Build sfrxcli stdin commands (no --env in interactive mode)
        cmds_for_stdin = []
        for st_type in setting_types:
            cmds_for_stdin.append(f'ds --import --setting-type {st_type} --static-file-directory "{static_local}"')
        cmds_for_stdin.append('exit')

        # Temp file paths
        output_local = os.path.join(static_local, f"ds_import_output_{timestamp}.txt")
        output_unc   = os.path.join(static_unc, f"ds_import_output_{timestamp}.txt")
        script_local = os.path.join(static_local, f"run_ds_import_{timestamp}.ps1")
        script_unc   = os.path.join(static_unc, f"run_ds_import_{timestamp}.ps1")

        # Build PS1 script that pipes stdin to sfrxcli
        ps1_lines = [
            f"$exe = '{_ps_sq(remote_exe)}'",
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
            ps1_lines.append(f"    $p.StandardInput.WriteLine('{_ps_sq(cmd)}')")
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

        task_name = f"SFRxDSImport_{timestamp}"
        tr = f'powershell -NoProfile -ExecutionPolicy Bypass -File "{script_local}"'

        log_lines.append(f"\nCLI bin: {cli_bin_local}")
        log_lines.append(f"Static dir: {static_local}")
        log_lines.append("=" * 50 + "\nOutput:\n")

        # Create remote scheduled task
        create_r = subprocess.run(
            ["schtasks", "/create", "/s", remote_host,
             "/u", remote_username, "/p", remote_password,
             "/tn", task_name, "/tr", tr,
             "/sc", "ONCE", "/st", "00:00",
             "/ru", remote_username, "/rp", remote_password, "/f"],
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

        log_lines.append(f"Task '{task_name}' started on {remote_host}. Waiting for completion...\n")

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

        # Clean up
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
        return {"success": False, "output": '\n'.join(log_lines), "error": error_msg, "log_file": log_file_path or "N/A"}