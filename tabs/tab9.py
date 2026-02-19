import subprocess
from pathlib import Path

import streamlit as st


ALLOWED_SCRIPT_EXTENSIONS = {".bat", ".cmd", ".ps1"}


def render_tab9() -> None:
    st.subheader("Service Restarts")
    st.info(
        "Run this on the server that hosts the SmartFactory Rx services (usually the upper/ENV server)."
    )

    site_name = st.session_state.get("site_name", "").strip()

    if not site_name:
        st.warning("Please set the site name in Setup Steps (Tab 1) before running the restart script.")
        return

    base_dir = Path(r"E:\Applied Materials\SFRxServiceRestarts")
    script_candidates = []

    if base_dir.exists():
        for entry in base_dir.iterdir():
            if entry.is_file() and entry.suffix.lower() in ALLOWED_SCRIPT_EXTENSIONS:
                if site_name.lower() in entry.name.lower():
                    script_candidates.append(entry)

    default_script = script_candidates[0] if script_candidates else base_dir / f"{site_name}_SFRxServiceRestarts.bat"

    st.markdown("**Instance-specific restart script**")
    script_path_str = st.text_input(
        "Path to restart script",
        value=str(default_script),
        help="Located under E:\\Applied Materials\\SFRxServiceRestarts. Adjust if your file is named differently (e.g., .ps1).",
    )

    test_mode = st.checkbox("🧪 Test Mode (do not execute, just simulate)", value=False, key="restart_services_test_mode")

    def _run_restart_script():
        script_path = Path(script_path_str.strip().strip('"'))

        if not script_path.exists():
            st.error(f"Script not found: {script_path}")
            return

        if script_path.suffix.lower() not in ALLOWED_SCRIPT_EXTENSIONS:
            st.warning(f"Unexpected script extension: {script_path.suffix}. Proceeding anyway.")

        if test_mode:
            st.success(f"[TEST MODE] Would execute: {script_path}")
            return

        cmd = (
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
            if script_path.suffix.lower() == ".ps1"
            else [str(script_path)]
        )

        with st.spinner(f"Running restart script for site {site_name}..."):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    shell=True,
                )
                if result.returncode == 0:
                    st.success("✅ Restart script completed successfully")
                    if result.stdout:
                        st.text_area("Script output", result.stdout, height=200)
                else:
                    st.error(
                        f"❌ Restart script failed (exit {result.returncode})\n\n{result.stderr or result.stdout}"
                    )
            except Exception as exc:
                st.error(f"Error running restart script: {exc}")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶️ Run Restart Script", type="primary", use_container_width=True):
            _run_restart_script()

        if st.button("⚡ Execute Restart Action", use_container_width=True):
            _run_restart_script()
