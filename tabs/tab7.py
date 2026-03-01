import streamlit as st
import os
import subprocess
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
        Run on the upper server. Commands will execute in `{cli_path}` automatically.

        1. Click **Generate Commands** to create the CLI import commands.
        2. Review the generated commands.
        3. Click **Run CLI Import Commands** to execute them automatically.
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

        st.markdown("---")

        test_mode = st.checkbox("Test Mode (simulate CLI execution without sfrxcli)", value=False, key="cli_import_test_mode")
        if test_mode:
            st.info("Test mode enabled - will simulate CLI execution for testing purposes")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Run CLI Import Commands", type="primary", use_container_width=True):
                try:
                    site_name = st.session_state.get("site_name", "")
                    release_name = st.session_state.get("release_name", "")
                    equipments_file = st.session_state.get("equipments_file")
                    equipments_text = st.session_state.get("equipments_text", "")
                    test_mode = st.session_state.get("cli_import_test_mode", False)

                    base_path = _get_base_path()
                    if not base_path:
                        st.error("Please select the upper server in Setup Steps (Tab 1)")
                        st.stop()

                    migration_folder_path = os.path.join(
                        base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "Migration", release_name
                    )

                    with st.spinner("Running CLI import commands..." if not test_mode else "Simulating CLI import commands..."):
                        result = run_cli_import_commands(
                            site_name, release_name, migration_folder_path,
                            equipments_file, equipments_text, test_mode
                        )

                    if result["success"]:
                        st.success("Commands executed successfully!")
                        st.caption(f"Log file: {result['log_file']}")
                    else:
                        st.error(f"Error: {result['error']}")

                    if result["output"]:
                        st.markdown("### Command Output")
                        st.code(result["output"], language="text")

                except Exception as e:
                    st.error(f"Error running commands: {str(e)}")


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
    """Run CLI import commands on the upper server (mirrors tab3 run_cli_commands)."""
    import re, time

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

        commands_list = []
        for equipment in equipments:
            json_file = os.path.join(migration_local, f"{release_name}-{equipment}.json")
            csv_file  = os.path.join(migration_local, f"{release_name}-{equipment}.csv")
            commands_list.append(f'ie -if "{json_file}" --comment "{release_name}"')
            commands_list.append(f'is -if "{csv_file}" --comment "{release_name}"')
        commands_list.append('exit')
        commands_input = '\n'.join(commands_list)

        log_lines = [
            "=== CLI Import Commands Execution Log ===",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Site: {site_name}",
            f"Release: {release_name}",
            f"Mode: {'TEST (Simulated)' if test_mode else 'PRODUCTION'}",
            "=" * 50,
        ]

        if test_mode:
            log_lines.append(f"\n[TEST MODE] Commands to execute:\n{commands_input}\n")
            simulated = [
                "SmartFactoryRx CLI v2.5.1",
                f"Connecting to environment: {site_name}...",
                f"Connected successfully to {site_name}",
                "",
            ]
            for equipment in equipments:
                simulated.append(f"Importing: {equipment}")
                simulated.append(f"  ie ({release_name}-{equipment}.json) ... Done")
                simulated.append(f"  is ({release_name}-{equipment}.csv) ... Done")
                simulated.append("")
            simulated.append("All imports completed successfully!")
            simulated.append("Session closed.")
            full_output = '\n'.join(simulated)
            log_lines.append(full_output)
            log_lines.append(f"\n{'=' * 50}")
            log_lines.append("[TEST MODE] Simulated exit code: 0")
            log_lines.append(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_lines))
            return {"success": True, "output": full_output, "error": None, "log_file": log_file_path}

        if not upper_base:
            return {"success": False, "output": "", "error": "Upper server base path is required in Setup (Tab 1)", "log_file": log_file_path}

        cli_bin_unc   = os.path.join(upper_base, "Applied Materials", f"SmartFactoryRx_{site_name}", "CLI", "bin")
        cli_bin_local = _unc_to_local(cli_bin_unc)
        remote_exe    = os.path.join(cli_bin_local, "sfrxcli.exe")
        remote_host   = _host_from_unc(upper_base)

        if not remote_host:
            raise RuntimeError("Could not determine remote host from upper base path")

        log_lines.append(f"\nCLI bin directory: {cli_bin_local}")
        log_lines.append(f"Commands to execute:\n{commands_input}\n")
        log_lines.append("=" * 50)
        log_lines.append("\nOutput:\n")

        cmd_lines = [ln.strip() for ln in commands_input.splitlines() if ln.strip() and ln.strip().lower() != 'exit']
        invocations = []
        for ln in cmd_lines:
            safe_exe = remote_exe.replace("'", "''")
            invocations.append(f"& '{safe_exe}' {ln} --env {site_name}")

        safe_cli_bin  = cli_bin_local.replace("'", "''")
        remote_script = f"cd '{safe_cli_bin}'; {'; '.join(invocations)}"

        remote_username = st.session_state.get("remote_username", "").strip()
        remote_password = st.session_state.get("remote_password", "")
        if remote_username and remote_password:
            safe_user  = remote_username.replace("'", "''")
            safe_pass  = remote_password.replace("'", "''")
            cred_setup = (
                f"$pass = ConvertTo-SecureString '{safe_pass}' -AsPlainText -Force; "
                f"$cred = New-Object System.Management.Automation.PSCredential('{safe_user}', $pass); "
            )
            cred_param = "-Credential $cred "
        else:
            cred_setup = ""
            cred_param = ""

        ps_cmd = f"{cred_setup}Invoke-Command -ComputerName {remote_host} {cred_param}-ScriptBlock {{ {remote_script} }}"

        try:
            ps_process = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=900
            )
            full_output = ps_process.stdout
            if ps_process.stderr:
                full_output += f"\n\nERRORS:\n{ps_process.stderr}"
            log_lines.append(full_output)
            log_lines.append(f"\n{'=' * 50}")
            returncode = ps_process.returncode

        except Exception as e_remote:
            log_lines.append(f"\n[WARN] Remote execution failed: {str(e_remote)}. Falling back to local.")
            cli_command = f'"{os.path.join(cli_bin_local, "sfrxcli.exe")}" -i --env {site_name}'
            process = subprocess.Popen(
                cli_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, shell=True, cwd=cli_bin_local
            )
            stdout, stderr = process.communicate(input=commands_input, timeout=300)
            full_output = stdout + (f"\n\nERRORS:\n{stderr}" if stderr else "")
            log_lines.append(full_output)
            log_lines.append(f"\n{'=' * 50}")
            returncode = process.returncode

        log_lines.append(f"Exit code: {returncode}")
        log_lines.append(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_lines))

        if returncode == 0:
            return {"success": True, "output": full_output, "error": None, "log_file": log_file_path}
        else:
            return {"success": False, "output": full_output, "error": "Command failed with non-zero exit code", "log_file": log_file_path}

    except subprocess.TimeoutExpired:
        error_msg = "Command execution timed out"
        log_lines.append(f"\n\nERROR: {error_msg}")
        try:
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_lines))
        except Exception:
            pass
        return {"success": False, "output": '\n'.join(log_lines), "error": error_msg, "log_file": log_file_path}
    except Exception as e:
        error_msg = str(e)
        log_lines.append(f"\n\nEXCEPTION: {error_msg}")
        try:
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_lines))
        except Exception:
            pass
        return {"success": False, "output": '\n'.join(log_lines), "error": error_msg, "log_file": log_file_path if 'log_file_path' in locals() else "N/A"}