import subprocess
import os
from datetime import datetime, timedelta
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
        start_time = (datetime.now() + timedelta(minutes=2)).strftime("%H:%M")

        with st.spinner(f"Running restart script on {upper_hostname}..."):
            try:
                # Step 1: Create scheduled task
                create_cmd = (
                    f'schtasks /create /tn "{task_name}" '
                    f'/tr "cmd /c \\"{local_script_path}\\"" '
                    f'/sc once /st {start_time} /ru SYSTEM '
                    f'/s {upper_hostname} /u {username} /p "{password}" /F'
                )
                st.text("Creating scheduled task...")
                result_create = subprocess.run(
                    create_cmd, capture_output=True, text=True, shell=True
                )
                if result_create.returncode != 0:
                    st.error(f"Failed to create task: {result_create.stderr or result_create.stdout}")
                    return
                st.text(f"✓ Task created: {task_name}")

                # Step 2: Run immediately
                run_cmd = (
                    f'schtasks /run /tn "{task_name}" '
                    f'/s {upper_hostname} /u {username} /p "{password}"'
                )
                st.text("Running task...")
                result_run = subprocess.run(
                    run_cmd, capture_output=True, text=True, shell=True
                )
                if result_run.returncode != 0:
                    st.error(f"Failed to run task: {result_run.stderr or result_run.stdout}")
                else:
                    st.text("✓ Task started")

                # Step 3: Wait and check status
                import time
                time.sleep(5)

                query_cmd = (
                    f'schtasks /query /tn "{task_name}" /fo LIST '
                    f'/s {upper_hostname} /u {username} /p "{password}"'
                )
                result_query = subprocess.run(
                    query_cmd, capture_output=True, text=True, shell=True
                )
                if result_query.stdout:
                    st.text_area("Task status", result_query.stdout, height=150)

                # Step 4: Delete the task
                delete_cmd = (
                    f'schtasks /delete /tn "{task_name}" /f '
                    f'/s {upper_hostname} /u {username} /p "{password}"'
                )
                result_delete = subprocess.run(
                    delete_cmd, capture_output=True, text=True, shell=True
                )
                if result_delete.returncode == 0:
                    st.text("✓ Task cleaned up")

                st.success(f"✅ Restart script executed on {upper_hostname}")

            except Exception as exc:
                st.error(f"Error: {exc}")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶️ Run Restart Script", type="primary", use_container_width=True):
            _run_restart_script()
