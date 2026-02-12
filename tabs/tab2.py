import streamlit as st
import os
from pathlib import Path


def render_tab2() -> None:
    st.markdown("""
    1. Open the E3 (EES) Launcher.
    2. Log in using an account with administrative privileges.
    3. On the "Administration" tab, select the "Import/Export" option.
    4. Select the E3 Objects outlined in the E3Objects.xlsx file located in <Migration Folder>.
    5. Click on the "Export" button at the top of the screen, name the file <Release Name>.e3pkg, 
       and save the export package to the <Migration Folder> directory. You can upload the file here as well.
    """)
    
    st.markdown("---")
    
    st.subheader("Upload your e3pkg File")
    
    e3pkg_file = st.file_uploader(
        "Select your e3pkg file",
        type=["e3pkg"],
        key="e3pkg_file",
        label_visibility="collapsed"
    )
    
    if e3pkg_file:
        st.success(f"✓ {e3pkg_file.name} uploaded successfully")
    
    st.markdown("---")
    
    # Save file button (centered)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 Save File to Migration Folder", type="primary", use_container_width=True):
            base_drive = st.session_state.get("base_drive", "").strip()
            release_name = st.session_state.get("release_name", "").strip()
            e3pkg_file_from_state = st.session_state.get("e3pkg_file")
            
            if not base_drive or not release_name:
                st.error("Please complete the setup information in Tab 1 (base drive and release name)")
            elif not e3pkg_file_from_state:
                st.error("Please upload an e3pkg file first")
            else:
                try:
                    # Build the migration path - ensure backslash after drive letter
                    base_path = base_drive + "\\" if not base_drive.endswith("\\") else base_drive
                    migration_path = os.path.join(base_path, "Applied Materials", "SmartFactoryRx_Westport", "Migration", release_name)
                    
                    # Create the directory if it doesn't exist
                    Path(migration_path).mkdir(parents=True, exist_ok=True)
                    
                    # Save the e3pkg file
                    file_path = os.path.join(migration_path, e3pkg_file_from_state.name)
                    
                    # Reset file pointer to beginning before reading
                    e3pkg_file_from_state.seek(0)
                    
                    with open(file_path, "wb") as f:
                        f.write(e3pkg_file_from_state.getbuffer())
                    
                    # Verify file was written
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        st.success(f"✅ File saved successfully!\n\nPath: {file_path}\nSize: {file_size} bytes")
                    else:
                        st.error("File was not saved. Please check the path and try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

