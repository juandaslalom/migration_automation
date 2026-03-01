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
        3. Click **▶️ Run CLI Import Commands** to execute them automatically.
        """
    )

    def _get_base_path() -> str:
        upper_base_val = st.session_state.get("upper_base_path", "").strip()
        return upper_base_val.rstrip("\\/") if upper_base_val else ""

    # Generate Commands button
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

    # Display commands text box
    if 'cli_import_commands' in st.session_state and st.session_state['cli_import_commands']:
        st.text_area(
            "Generated Commands:",
            value=st.session_state['cli_import_commands'],
            height=300,
            disabled=True,
            key="cli_import_commands_display"
        )

        st.markdown("---")

        test_mode = st.checkbox("🧪 Test Mode (simulate CLI execution without sfrxcli)", value=False, key="cli_import_test_mode")
        if test_mode:
            st.info("ℹ️ Test mode enabled - will simulate CLI execution for testing purposes")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("▶️ Run CLI Import Commands", type="primary", use_container_width=True):
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
                        st.success(f"✅ Commands executed successfully!")
                        st.caption(f"Log file: {result['log_file']}")
                    else:
                        st.error(f"❌ Error: {result['error']}")

                    if result["output"]:
                        st.markdown("### 💻 Command Output")
                        st.code(result["output"], language="text")

                except Exception as e:
                    st.error(f"Error running commands: {str(e)}")


def generate_cli_import_commands(site_name: str, release_name: str, migration_folder_path: str, equipments_file, equipments_text: str) -> str:
    """Generate CLI import commands preview (non-interactive Invoke-Command format)."""
    equipments = []
    if equipments_file:
        content = equipments_file.getvalue().decode("utf-8")
        equipments = [line.strip() for line in content.splitlines() if line.strip()]
    elif equipments_text:
        equipments = [line.strip() for line in equipments_text.splitlines() if line.strip()]

    remote_host = _host_from_unc(migration_folder_path)
    if not remote_host:
        remote_host = "<upper-server>"

    cli_bin_local = _unc_to_local(
        os.path.join(
            migration_folder_path.split("Migration")[0].rstrip("\\"),
            "..\\CLI\\bin"
        )
    )

    lines = [f"# Runs on: {remote_host} via Invoke-Command (non-interactive)", ""]
    for equipment in equipments:
        json_file = os.path.join(migration_folder_path, f"{release_name}-{equipment}.json")
        csv_file  = os.path.join(migration_folder_path, f"{release_name}-{equipment}.csv")
        json_local = _unc_to_local(json_file)
        csv_local  = _unc_to_local(csv_file)
        lines.append(f"& '<cli_bin>\\sfrxcli.exe' ie -if \"{json_local}\" --comment \"{release_name}\" --env {site_name}")
        lines.append(f"& '<cli_bin>\\sfrxcli.exe' is -if \"{csv_local}\" --comment \"{release_name}\" --env {site_name}")
        lines.append("")

    return "\n".join(lines)


def run_cli_import_commands(site_name: str, release_name: str, migration_folder_path: str, equipments_file, equipments_text: str, test_mode: bool = False) -> dict:
    """Run CLI import commands on the upper server via non-interactive Invoke-Command."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = os.path.join(migration_folder_path, f"{release_name}_cli_import_log_{timestamp}.log")

    log_lines = [
        "=== CLI Import Commands Execution Log ===",
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Site: {site_name}",
        f"Release: {release_name}",
        f"Mode: {'TEST (Simulated)' if test_mode else 'PRODUCTION'}",
        "=" * 50,
    ]

    try:
        # Build equipment list
        equipments = []
        if equipments_file:
            content = equipments_file.getvalue().decode("utf-8")
            equipments = [l.strip() for l in content.splitlines() if l.strip()]
        elif equipments_text:
            equipments = [l.strip() for l in equipments_text.splitlines() if l.strip()]

        # Derive remote host and local paths on the upper server
        remote_host = _host_from_unc(migration_folder_path)
        if not remote_host:
            raise RuntimeError("Could not determine upper server hostname from base path")

        migration_local = _unc_to_local(migration_folder_path)

        # Derive CLI bin path (local to upper server)
        upper_base_unc = st.session_state.get("upper_base_path", "").strip().rstrip("\\")
        cli_bin_unc = os.path.join(upper_base_unc, "Applied Materials", f"SmartFactoryRx_{site_name}", "CLI", "bin")
        cli_bin_local = _unc_to_local(cli_bin_unc)
        remote_exe = os.path.join(cli_bin_local, "sfrxcli.exe")

        log_lines.append(f"\nRemote host: {remote_host}")
        log_lines.append(f"CLI bin (local to server): {cli_bin_local}")
        log_lines.append(f"Migration path (local to server): {migration_local}")
        log_lines.append("=" * 50)

        if test_mode:
            # Simulate output
            simulated = [
                f"SmartFactoryRx CLI - TEST MODE",
                f"Would execute on: {remote_host}",
                "",
            ]
            for equipment in equipments:
                simulated.append(f"[SIMULATED] ie: {release_name}-{equipment}.json -> OK")
                simulated.append(f"[SIMULATED] is: {release_name}-{equipment}.csv -> OK")
            simulated.append("\nAll imports simulated successfully.")
            full_output = "\n".join(simulated)
            log_lines.append(full_output)
            log_content = "\n".join(log_lines)
            try:
                with open(log_file_path, 'w', encoding='utf-8') as f:
                    f.write(log_content)
            except Exception:
                pass
            return {"success": True, "output": full_output, "error": None, "log_file": log_file_path}

        # ── Production: WinRM-free via net use + wmic ──────────────────────────
        # Invoke-Command (WinRM) is not used — it may hang if WinRM is unavailable.
        # Approach:
        #  1. Authenticate to E$ share with net use
        #  2. Write a .bat into the migration folder via UNC
        #  3. Launch it on the remote server via wmic process call create (DCOM)
        #  4. Poll the output file until the done-sentinel appears (max 10 min)
        #  5. Read the output, clean up temp files, disconnect share
        remote_username = st.session_state.get("remote_username", "").strip()
        remote_password = st.session_state.get("remote_password", "")

        share_path = f"\\\\{remote_host}\\e$"
        net_use_cmd = ["net", "use", share_path]
        if remote_username:
            net_use_cmd += [f"/user:{remote_username}", remote_password or ""]
        subprocess.run(net_use_cmd, capture_output=True, text=True, timeout=30)

        bat_unc  = os.path.join(migration_folder_path, f"{release_name}_cli_import_{timestamp}.bat")
        out_unc  = os.path.join(migration_folder_path, f"{release_name}_cli_import_{timestamp}.txt")
        bat_local = _unc_to_local(bat_unc)   # path as seen by the remote server
        out_local = _unc_to_local(out_unc)
        sentinel  = "SFRXCLI_IMPORT_DONE"

        bat_lines = ["@echo off", f'cd /d "{cli_bin_local}"']
        for equipment in equipments:
            json_local = os.path.join(migration_local, f"{release_name}-{equipment}.json")
            csv_local  = os.path.join(migration_local, f"{release_name}-{equipment}.csv")
            bat_lines.append(f'"{remote_exe}" ie -if "{json_local}" --comment "{release_name}" --env {site_name} >> "{out_local}" 2>&1')
            bat_lines.append(f'"{remote_exe}" is -if "{csv_local}" --comment "{release_name}" --env {site_name} >> "{out_local}" 2>&1')
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

        # Poll for sentinel in the output file (max 10 minutes)
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
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write(log_content)
        except Exception:
            pass

        return {"success": True, "output": full_output, "error": None, "log_file": log_file_path}

    except TimeoutError as e:
        error_msg = str(e)
        log_lines.append(f"\nTIMEOUT: {error_msg}")
        try:
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(log_lines))
        except Exception:
            pass
        return {"success": False, "output": "\n".join(log_lines), "error": error_msg, "log_file": log_file_path}

    except Exception as e:
        error_msg = str(e)
        log_lines.append(f"\nEXCEPTION: {error_msg}")
        try:
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(log_lines))
        except Exception:
            pass
        return {"success": False, "output": "\n".join(log_lines), "error": error_msg, "log_file": log_file_path}


