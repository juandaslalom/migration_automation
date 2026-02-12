import streamlit as st
import os
from pathlib import Path


def render_tab1() -> None:
    # Input fields
    st.subheader("Setup Information")

    st.text_input(
        "Enter the site name",
        placeholder="<Site Name>",
        key="site_name"
    )

    st.selectbox(
        "Select the base drive",
        options=["C:", "D:", "E:"],
        key="base_drive",
        help="The drive where Applied Materials folder is located"
    )

    st.text_input(
        "Enter the release name (this will be the migration folder name)",
        placeholder="<Release Name>",
        key="release_name",
        help=r"Example: E:\Applied Materials\SmartFactoryRx_Westport\Migration\<Release Name>"
    )

    st.markdown("---")

    # File upload sections
    st.subheader("File Uploads")

    col1, col2 = st.columns(2)

    with col1:
        excel_file = st.file_uploader(
            "Upload your excel file",
            type=["xlsx", "xls"],
            key="excel_file"
        )
        if excel_file:
            st.success(f"✓ {excel_file.name} uploaded successfully")

    with col2:
        # Option to choose between file upload or text input
        input_method = st.radio(
            "Choose equipment input method:",
            ["Upload File", "Enter Text"],
            key="equipment_input_method",
            horizontal=True
        )
        
        if input_method == "Upload File":
            equipments_file = st.file_uploader(
                "Upload your equipments file",
                type="txt",
                key="equipments_file"
            )
            if equipments_file:
                st.success(f"✓ {equipments_file.name} uploaded successfully")
            
            # Show example format
            with st.expander("📄 Equipment file format example"):
                st.text("Each equipment on a new line:\nUPV8\nUPV9")
        else:
            st.text_area(
                "Enter equipment names (one per line)",
                placeholder="UPV8\nUPV9\nUPV10",
                key="equipments_text",
                height=150
            )
            if st.session_state.get("equipments_text"):
                equipment_count = len([e.strip() for e in st.session_state.equipments_text.split('\n') if e.strip()])
                st.success(f"✓ {equipment_count} equipment(s) entered")

    st.markdown("---")

    # Create folder and save file button (centered)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📁 Create Migration Folder and Save Excel File", type="primary", use_container_width=True):
            base_drive = st.session_state.get("base_drive", "").strip()
            release_name = st.session_state.get("release_name", "").strip()
            excel_file = st.session_state.get("excel_file")
            
            if not base_drive:
                st.error("Please enter the base drive")
            elif not release_name:
                st.error("Please enter the release name")
            elif not excel_file:
                st.error("Please upload an excel file first")
            else:
                try:
                    # Build the migration path - ensure backslash after drive letter
                    base_path = base_drive + "\\" if not base_drive.endswith("\\") else base_drive
                    migration_path = os.path.join(base_path, "Applied Materials", "SmartFactoryRx_Westport", "Migration", release_name)
                    
                    # Show the path that will be created
                    st.info(f"Creating folder at: {migration_path}")
                    
                    # Create the directory
                    Path(migration_path).mkdir(parents=True, exist_ok=True)
                    
                    # Verify the folder was created
                    if os.path.exists(migration_path):
                        st.success(f"✅ Folder created successfully at:\n{migration_path}")
                    
                    # Save the excel file
                    excel_path = os.path.join(migration_path, excel_file.name)
                    with open(excel_path, "wb") as f:
                        f.write(excel_file.getbuffer())
                    
                    if os.path.exists(excel_path):
                        st.success(f"✅ Excel file saved successfully at:\n{excel_path}")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    st.markdown("---")

    # Information message
    st.info(
        """
        **Note:** Provide evidence of the Strategy validation/approval included in the Release 
        Migration via an email screen capture.
        """
    )
