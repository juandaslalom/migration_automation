import streamlit as st
import subprocess
import time


def render_tab6() -> None:
    st.subheader("E3 Object Migration – E3 Import")
    
    st.markdown("""
    ### Instructions:
    
    1. Open the E3 (EES) Launcher.
    2. Log in using an account with administrative privileges.
    3. On the "Administration" tab, select the "Import/Export" option.
    4. Click the "Import" button and open the .e3pkg file located in Migration Folder.
    5. Click on the "Check Mapping" button at the bottom of the screen.
    6. Once the mapping of all the objects has been verified, click the "Import" button.
    7. Take a screen capture of the results.
    8. Restart the following services using the Windows Services console:
        - `SFRx_<Site>_E3Client`
        - `SFRx_<Site>_Portal`
    """)
    
    st.markdown("---")
    st.markdown("### Step 8: Restart Services")
    
    # Test mode toggle
    test_mode = st.checkbox("🧪 Test Mode (simulate without real services)", value=False, key="service_test_mode")

    # Get site name from session state
    site_name = st.session_state.get("site_name", "")

    if not site_name:
        st.warning("⚠️ Please complete Setup Steps (Tab 1) to set the site name first.")
    else:
        st.info(f"Site: **{site_name}**" + (" | **TEST MODE**" if test_mode else ""))

        def _restart_service(service_name: str) -> bool:
            """Restart a Windows service; simulate when test_mode is on."""
            if test_mode:
                time.sleep(1)
                st.success(f"✅ {service_name} restarted (simulated)")
                return True
            try:
                stop_result = subprocess.run(
                    ["net", "stop", service_name],
                    capture_output=True,
                    text=True,
                    shell=True,
                )

                start_result = subprocess.run(
                    ["net", "start", service_name],
                    capture_output=True,
                    text=True,
                    shell=True,
                )

                if start_result.returncode == 0:
                    st.success(f"✅ {service_name} restarted")
                    return True
                st.error(f"❌ Failed to restart {service_name}\n\n{start_result.stderr}")
                return False
            except Exception as e:
                st.error(f"Error restarting {service_name}: {str(e)}")
                return False

        st.markdown("---")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Restart E3Client then Portal", type="primary", use_container_width=True):
                e3_client_service = f"SFRx_{site_name}_E3Client"
                portal_service = f"SFRx_{site_name}_Portal"

                with st.spinner("Restarting services in order..."):
                    first_ok = _restart_service(e3_client_service)

                    if first_ok:
                        st.info("Waiting 7 seconds before restarting Portal...")
                        time.sleep(7)
                        _restart_service(portal_service)
