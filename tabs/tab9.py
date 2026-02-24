import subprocess
from pathlib import Path

import streamlit as st


def render_tab9() -> None:
    st.subheader("Service Restarts")
    st.info(
        "Run this on the server that hosts the SmartFactory Rx services (upper server)."
    )

    site_name = st.session_state.get("site_name", "").strip()

    if not site_name:
        st.warning("Please set the site name in Setup Steps (Tab 1) before running the restart script.")
        return

    base_dir = Path(r"E:\Applied Materials\SFRxServiceRestarts")
    script_path = base_dir / f"{site_name}ServiceRestart.bat"

    st.markdown("**Restart script**")
    st.caption(f"Expected location: {script_path}")

    test_mode = st.checkbox("🧪 Test Mode (do not execute, just simulate)", value=False, key="restart_services_test_mode")

    def _run_restart_script():
        if not script_path.exists():
            st.error(f"Script not found: {script_path}")
            return

        if test_mode:
            st.success(f"[TEST MODE] Would execute: {script_path}")
            return

        cmd = [str(script_path)]

        with st.spinner(f"Running restart script for site {site_name}..."):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    shell=True,
                )
                output = result.stdout or ""
                error_output = result.stderr or ""

                if result.returncode == 0:
                    st.success("✅ Restart script completed successfully")
                else:
                    st.error(f"❌ Restart script failed (exit {result.returncode})")

                if output or error_output:
                    combined = output + ("\n" if output and error_output else "") + error_output
                    st.text_area("Script output", combined, height=220)
            except Exception as exc:
                st.error(f"Error running restart script: {exc}")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶️ Run Restart Script", type="primary", use_container_width=True):
            _run_restart_script()
