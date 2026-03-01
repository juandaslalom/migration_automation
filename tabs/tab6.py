import streamlit as st
import subprocess
import time


def render_tab6() -> None:
    st.subheader("E3 Object Migration – E3 Import")

    st.markdown("""
    ### Instructions:

    1. Open the E3 (EES) Launcher on the **upper server**.
    2. Log in using an account with administrative privileges.
    3. On the "Administration" tab, select the "Import/Export" option.
    4. Click the "Import" button and open the .e3pkg file located in Migration Folder.
    5. Click on the "Check Mapping" button at the bottom of the screen.
    6. Once the mapping of all the objects has been verified, click the "Import" button.
    7. Take a screen capture of the results.
    8. Restart the following services on the **upper server** using the button below:
        - `SFRx_<Site>_E3Client`
        - `SFRx_<Site>_Portal`
    """)

    st.markdown("---")
    st.markdown("### Step 8: Restart Services on Upper Server")

    # Test mode toggle
    test_mode = st.checkbox("🧪 Test Mode (simulate without real services)", value=False, key="service_test_mode")

    site_name = st.session_state.get("site_name", "")
    upper_base = st.session_state.get("upper_base_path", "").strip()
    remote_username = st.session_state.get("remote_username", "").strip()
    remote_password = st.session_state.get("remote_password", "")

    # Derive upper hostname from UNC base path (e.g. \\WA01928Q\e$)
    upper_hostname = None
    if upper_base:
        try:
            upper_hostname = upper_base.lstrip("\\").split("\\")[0]
        except Exception:
            upper_hostname = None

    if not site_name:
        st.warning("⚠️ Please complete Setup Steps (Tab 1) to set the site name first.")
    elif not upper_hostname:
        st.warning("⚠️ Please select the upper server in Tab 1.")
    else:
        st.info(
            f"Upper server: **{upper_hostname}**  |  Site: **{site_name}**"
            + (" | **TEST MODE**" if test_mode else "")
        )

        def _restart_service_remote(service_name: str, hostname: str) -> bool:
            """Restart a Windows service on a remote host via sc \\hostname."""
            if test_mode:
                time.sleep(1)
                st.success(f"✅ {service_name} restarted on {hostname} (simulated)")
                return True
            try:
                stop_result = subprocess.run(
                    ["sc", f"\\\\{hostname}", "stop", service_name],
                    capture_output=True, text=True
                )
                time.sleep(3)  # brief wait after stop
                start_result = subprocess.run(
                    ["sc", f"\\\\{hostname}", "start", service_name],
                    capture_output=True, text=True
                )
                if start_result.returncode == 0:
                    st.success(f"✅ {service_name} restarted on {hostname}")
                    return True
                st.error(f"❌ Failed to restart {service_name} on {hostname}:\n{start_result.stdout or start_result.stderr}")
                return False
            except Exception as e:
                st.error(f"Error restarting {service_name}: {str(e)}")
                return False

        st.markdown("---")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Restart E3Client then Portal", type="primary", use_container_width=True):
                if not test_mode and (not remote_username or not remote_password):
                    st.error("❌ Please enter remote credentials in Tab 1 (Remote Credentials section).")
                    st.stop()

                e3_client_service = f"SFRx_{site_name}_E3Client"
                portal_service = f"SFRx_{site_name}_Portal"

                # Establish authenticated SMB session so sc can authenticate
                ipc_share = f"\\\\{upper_hostname}\\IPC$"
                if not test_mode:
                    subprocess.run(["net", "use", ipc_share, "/delete", "/yes"], capture_output=True)
                    connect = subprocess.run(
                        ["net", "use", ipc_share, f"/user:{remote_username}", remote_password],
                        capture_output=True, text=True
                    )
                    if connect.returncode != 0:
                        st.error(f"❌ Could not authenticate to {upper_hostname}:\n{connect.stderr or connect.stdout}")
                        st.stop()

                with st.spinner(f"Restarting services on {upper_hostname}..."):
                    first_ok = _restart_service_remote(e3_client_service, upper_hostname)
                    if first_ok:
                        st.info("⏳ Waiting 7 seconds before restarting Portal...")
                        time.sleep(7)
                        _restart_service_remote(portal_service, upper_hostname)

                # Clean up IPC$ session
                if not test_mode:
                    subprocess.run(["net", "use", ipc_share, "/delete", "/yes"], capture_output=True)
