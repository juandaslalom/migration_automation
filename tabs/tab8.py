import streamlit as st
import os
import subprocess
import time
from datetime import datetime


def _unc_to_local(p: str) -> str:
    """Convert \\\\hostname\\e$\\foo\\bar → E:\\foo\\bar"""
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

    st.info("Run this CLI Import on the **upper server**. Switch to the upper server before executing these commands.")

    # Instructions and effective CLI path (shown upfront)
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
        Commands will be executed in `{cli_path}` automatically.

        1. Click **Generate Commands** to create the Dashboard CLI import commands.
        2. Review the generated commands.
        3. Click **▶️ Run Dashboard CLI Commands** to execute them automatically.

        **Commands will import:**
        - Process Map domain settings
        - Equipment Health domain settings
        - Equipment View domain settings
        - Operation domain settings
        """
    )

    def _get_base_path() -> str:
        """Resolve upper server base path from Tab 1 selection."""
        upper_base_val = st.session_state.get("upper_base_path", "").strip()
        if upper_base_val:
            return upper_base_val.rstrip("\\/")
        return ""
    
    # Generate Commands button
    if st.button("Generate Commands", key="generate_dashboard_cli_commands"):
        # Get data from session state
        site_name = st.session_state.get("site_name", "")
        
        # Validate inputs
        if not site_name:
            st.error("Please enter the site name in Setup Steps (Tab 1)")
        elif not _get_base_path():
            st.error("Please select the upper server in Setup Steps (Tab 1)")
        else:
            try:
                # Generate commands logic here
                base_root = _get_base_path()
                commands = generate_dashboard_cli_commands(site_name, base_root)
                st.session_state['dashboard_cli_commands'] = commands
            except Exception as e:
                st.error(f"Error generating commands: {str(e)}")
    
    # Display commands text box
    if 'dashboard_cli_commands' in st.session_state and st.session_state['dashboard_cli_commands']:
        st.text_area(
            "Generated Commands:",
            value=st.session_state['dashboard_cli_commands'],
            height=300,
            disabled=True,
            key="dashboard_cli_commands_display"
        )
        
        st.markdown("---")

        test_mode = st.checkbox("🧪 Test Mode (simulate CLI execution without sfrxcli)", value=False, key="dashboard_cli_test_mode")
        if test_mode:
            st.info("ℹ️ Test mode enabled - will simulate CLI execution for testing purposes")

        # Run Dashboard CLI Commands button (centered)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("▶️ Run Dashboard CLI Commands", type="primary", use_container_width=True):
                try:
                    site_name = st.session_state.get("site_name", "")
                    test_mode = st.session_state.get("dashboard_cli_test_mode", False)

                    base_root = _get_base_path()
                    if not base_root:
                        st.error("Please select the upper server in Setup Steps (Tab 1)")
                        st.stop()
                    log_folder_path = os.path.join(
                        base_root, "Applied Materials", f"SmartFactoryRx_{site_name}", "Portal", "data", "static"
                    )

                    with st.spinner("Running Dashboard CLI commands..." if not test_mode else "Simulating Dashboard CLI commands..."):
                        result = run_dashboard_cli_commands(site_name, base_root, log_folder_path, test_mode)
                    
                    if result["success"]:
                        st.success(f"✅ Commands executed successfully!\n\nLog file: {result['log_file']}")
                    else:
                        st.error(f"❌ Error: {result['error']}")
                    
                    # Always show output in terminal-like interface
                    if result["output"]:
                        st.markdown("### 💻 Command Output")
                        st.code(result["output"], language="bash")
                    
                except Exception as e:
                    st.error(f"Error running commands: {str(e)}")
    


def generate_dashboard_cli_commands(site_name: str, base_drive: str) -> str:
    """Generate Dashboard CLI import commands (non-interactive Invoke-Command format)."""
    if base_drive.startswith("\\"):
        base_path = base_drive.rstrip("\\/")
    else:
        base_path = base_drive.rstrip("\\/")

    static_directory = os.path.join(
        base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "Portal", "data", "static"
    )
    static_local = _unc_to_local(static_directory)

    remote_host = _host_from_unc(base_drive) or "<upper-server>"
    cli_bin_unc = os.path.join(base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "CLI", "bin")
    cli_bin_local = _unc_to_local(cli_bin_unc)

    setting_types = ["ProcessMap", "EquipmentHealth", "EquipmentView", "Operation"]
    lines = [f"# Runs on: {remote_host} via Invoke-Command (non-interactive)", ""]
    for st_type in setting_types:
        safe_dir = static_local.replace('"', '""')
        lines.append(
            f'& \'{cli_bin_local}\\sfrxcli.exe\' ds --import --setting-type {st_type} '
            f'--static-file-directory "{safe_dir}" --env {site_name}'
        )
        lines.append("")

    return "\n".join(lines)


def run_dashboard_cli_commands(site_name: str, base_drive: str, log_folder_path: str, test_mode: bool = False) -> dict:
    """Run Dashboard CLI import commands on the upper server via non-interactive Invoke-Command."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = os.path.join(log_folder_path, f"dashboard_cli_import_log_{timestamp}.log")

    log_lines = [
        "=== Dashboard CLI Import Commands Execution Log ===",
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Site: {site_name}",
        f"Mode: {'TEST (Simulated)' if test_mode else 'PRODUCTION'}",
        "=" * 50,
    ]

    try:
        # Resolve paths
        if base_drive.startswith("\\"):
            base_path = base_drive.rstrip("\\/")
        else:
            base_path = base_drive.rstrip("\\/")

        remote_host = _host_from_unc(base_drive)
        if not remote_host:
            raise RuntimeError("Could not determine upper server hostname from base path")

        cli_bin_unc = os.path.join(base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "CLI", "bin")
        cli_bin_local = _unc_to_local(cli_bin_unc)
        remote_exe = os.path.join(cli_bin_local, "sfrxcli.exe")

        static_unc = os.path.join(base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "Portal", "data", "static")
        static_local = _unc_to_local(static_unc)

        setting_types = ["ProcessMap", "EquipmentHealth", "EquipmentView", "Operation"]

        log_lines.append(f"\nRemote host: {remote_host}")
        log_lines.append(f"CLI bin (local to server): {cli_bin_local}")
        log_lines.append(f"Static directory (local to server): {static_local}")
        log_lines.append("=" * 50)

        if test_mode:
            simulated = [
                "SmartFactoryRx CLI - TEST MODE",
                f"Would execute on: {remote_host}",
                "",
            ]
            for st_type in setting_types:
                simulated.append(f"[SIMULATED] ds --import --setting-type {st_type} -> OK")
            simulated.append("\nAll dashboard imports simulated successfully.")
            full_output = "\n".join(simulated)
            log_lines.append(full_output)
            log_content = "\n".join(log_lines)
            try:
                os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
                with open(log_file_path, 'w', encoding='utf-8') as f:
                    f.write(log_content)
            except Exception:
                pass
            return {"success": True, "output": full_output, "error": None, "log_file": log_file_path}

        # ── Production: WinRM-free via net use + wmic ──────────────────────────
        remote_username = st.session_state.get("remote_username", "").strip()
        remote_password = st.session_state.get("remote_password", "")

        share_path = f"\\\\{remote_host}\\e$"
        net_use_cmd = ["net", "use", share_path]
        if remote_username:
            net_use_cmd += [f"/user:{remote_username}", remote_password or ""]
        subprocess.run(net_use_cmd, capture_output=True, text=True, timeout=30)

        bat_unc  = os.path.join(log_folder_path, f"dashboard_cli_{timestamp}.bat")
        out_unc  = os.path.join(log_folder_path, f"dashboard_cli_{timestamp}.txt")
        bat_local = _unc_to_local(bat_unc)
        out_local = _unc_to_local(out_unc)
        sentinel  = "SFRXCLI_DASHBOARD_DONE"

        bat_lines = ["@echo off", f'cd /d "{cli_bin_local}"']
        for st_type in setting_types:
            bat_lines.append(
                f'"{remote_exe}" ds --import --setting-type {st_type}'
                f' --static-file-directory "{static_local}" --env {site_name}'
                f' >> "{out_local}" 2>&1'
            )
        bat_lines.append(f'echo {sentinel} >> "{out_local}"')

        with open(bat_unc, 'w', encoding='utf-8') as f:
            f.write("\r\n".join(bat_lines))

        wmic_args = ["wmic", f"/node:{remote_host}"]
        if remote_username:
            wmic_args += [f"/user:{remote_username}", f"/password:{remote_password}"]
        wmic_args += ["process", "call", "create", f'cmd /c ""{bat_local}""']

        wmic_result = subprocess.run(wmic_args, capture_output=True, text=True, timeout=30)
        log_lines.append(f"wmic launch: {(wmic_result.stdout + wmic_result.stderr).strip()}")

        if wmic_result.returncode != 0:
            raise RuntimeError(f"wmic failed to launch remote process: {wmic_result.stderr or wmic_result.stdout}")

        # Poll for sentinel (max 10 minutes)
        max_wait, poll_interval, elapsed = 600, 5, 0
        full_output = ""
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            if os.path.exists(out_unc):
                try:
                    full_output = open(out_unc, 'r', encoding='utf-8', errors='replace').read()
                    if sentinel in full_output:
                        full_output = full_output.replace(sentinel, "").strip()
                        break
                except Exception:
                    pass
        else:
            raise TimeoutError(f"Remote execution did not complete within {max_wait}s")

        for tmp in (bat_unc, out_unc):
            try:
                os.remove(tmp)
            except Exception:
                pass
        subprocess.run(["net", "use", share_path, "/delete", "/yes"],
                       capture_output=True, text=True, timeout=15)

        log_lines.append(full_output)
        log_lines.append(f"\n{'=' * 50}")
        log_lines.append(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_content = "\n".join(log_lines)
        try:
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write(log_content)
        except Exception:
            pass

        return {"success": True, "output": full_output, "error": None, "log_file": log_file_path}

    except TimeoutError as e:
        error_msg = str(e)
        log_lines.append(f"\nTIMEOUT: {error_msg}")
        try:
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(log_lines))
        except Exception:
            pass
        return {"success": False, "output": "\n".join(log_lines), "error": error_msg, "log_file": log_file_path}

    except Exception as e:
        error_msg = str(e)
        log_lines.append(f"\nEXCEPTION: {error_msg}")
        try:
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(log_lines))
        except Exception:
            pass
        return {"success": False, "output": "\n".join(log_lines), "error": error_msg, "log_file": log_file_path}

    
