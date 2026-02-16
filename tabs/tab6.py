import streamlit as st
import subprocess
import time
from datetime import datetime, timedelta


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
        
        # Initialize last restart time in session state
        if "last_service_restart_time" not in st.session_state:
            st.session_state["last_service_restart_time"] = None
        
        # Check if 7 seconds have passed since last restart
        can_restart = True
        remaining_seconds = 0
        
        if st.session_state["last_service_restart_time"]:
            elapsed = (datetime.now() - st.session_state["last_service_restart_time"]).total_seconds()
            if elapsed < 7:
                can_restart = False
                remaining_seconds = int(7 - elapsed) + 1
        
        # Show waiting message if needed
        if not can_restart:
            st.warning(f"⏳ Please wait {remaining_seconds} more second(s) before restarting another service...")
            time.sleep(1)
            st.rerun()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Restart E3Client Service", use_container_width=True, disabled=not can_restart):
                service_name = f"SFRx_{site_name}_E3Client"
                with st.spinner(f"Restarting {service_name}..."):
                    if test_mode:
                        # Simulate service restart
                        time.sleep(2)
                        st.success(f"✅ {service_name} restarted successfully! (simulated)")
                        st.session_state["last_service_restart_time"] = datetime.now()
                    else:
                        try:
                            # Stop the service
                            stop_result = subprocess.run(
                                ["net", "stop", service_name],
                                capture_output=True,
                                text=True,
                                shell=True
                            )
                            
                            # Start the service
                            start_result = subprocess.run(
                                ["net", "start", service_name],
                                capture_output=True,
                                text=True,
                                shell=True
                            )
                            
                            if start_result.returncode == 0:
                                st.success(f"✅ {service_name} restarted successfully!")
                                # Update last restart time
                                st.session_state["last_service_restart_time"] = datetime.now()
                            else:
                                st.error(f"❌ Failed to restart {service_name}\n\n{start_result.stderr}")
                        except Exception as e:
                            st.error(f"Error restarting service: {str(e)}")
        
        with col2:
            if st.button("🔄 Restart Portal Service", use_container_width=True, disabled=not can_restart):
                service_name = f"SFRx_{site_name}_Portal"
                with st.spinner(f"Restarting {service_name}..."):
                    if test_mode:
                        # Simulate service restart
                        time.sleep(2)
                        st.success(f"✅ {service_name} restarted successfully! (simulated)")
                        st.session_state["last_service_restart_time"] = datetime.now()
                    else:
                        try:
                            # Stop the service
                            stop_result = subprocess.run(
                                ["net", "stop", service_name],
                                capture_output=True,
                                text=True,
                                shell=True
                            )
                            
                            # Start the service
                            start_result = subprocess.run(
                                ["net", "start", service_name],
                                capture_output=True,
                                text=True,
                                shell=True
                            )
                            
                            if start_result.returncode == 0:
                                st.success(f"✅ {service_name} restarted successfully!")
                                # Update last restart time
                                st.session_state["last_service_restart_time"] = datetime.now()
                            else:
                                st.error(f"❌ Failed to restart {service_name}\n\n{start_result.stderr}")
                        except Exception as e:
                            st.error(f"Error restarting service: {str(e)}")
        
        st.markdown("---")
        
        # Option to restart both at once
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Restart Both Services", type="primary", use_container_width=True, disabled=not can_restart):
                services = [
                    f"SFRx_{site_name}_E3Client",
                    f"SFRx_{site_name}_Portal"
                ]
                
                with st.spinner("Restarting services..."):
                    if test_mode:
                        # Simulate both services restart
                        for service_name in services:
                            time.sleep(1)
                            st.success(f"✅ {service_name} restarted (simulated)")
                        st.success("✅ All services restarted successfully! (simulated)")
                        st.session_state["last_service_restart_time"] = datetime.now()
                    else:
                        all_success = True
                        for service_name in services:
                            try:
                                # Stop the service
                                subprocess.run(
                                    ["net", "stop", service_name],
                                    capture_output=True,
                                    text=True,
                                    shell=True
                                )
                                
                                # Start the service
                                start_result = subprocess.run(
                                    ["net", "start", service_name],
                                    capture_output=True,
                                    text=True,
                                    shell=True
                                )
                                
                                if start_result.returncode != 0:
                                    st.error(f"❌ Failed to restart {service_name}")
                                    all_success = False
                                else:
                                    st.success(f"✅ {service_name} restarted")
                            except Exception as e:
                                st.error(f"Error restarting {service_name}: {str(e)}")
                                all_success = False
                        
                        if all_success:
                            st.success("✅ All services restarted successfully!")
                            # Update last restart time
                            st.session_state["last_service_restart_time"] = datetime.now()
