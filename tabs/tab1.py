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

    st.text_input(
        "Enter the release name",
        placeholder="<Release Name>",
        key="release_name"
    )

    st.text_input(
        "Enter the name of the migration folder",
        placeholder="<Migration Folder>",
        key="migration_folder"
    )

    st.text_input(
        "Enter the name of the migration folder path",
        placeholder="E.g., /path/to/migration/folder or C:\\path\\to\\migration\\folder",
        key="migration_folder_path"
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
        equipments_file = st.file_uploader(
            "Upload your equipments file",
            type="txt",
            key="equipments_file"
        )
        if equipments_file:
            st.success(f"✓ {equipments_file.name} uploaded successfully")
        
        # Show example format
        with st.expander("📄 Equipment file format example\n\nEach equipment on a new line:"):
            st.text("UPV8\nUPV9")

    st.markdown("---")

    # Create folder and save file button (centered)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📁 Create Migration Folder and Save Excel File", type="primary", use_container_width=True):
            migration_path = st.session_state.get("migration_folder_path", "")
            excel_file = st.session_state.get("excel_file")
            
            if not migration_path:
                st.error("Please enter the migration folder path")
            elif not excel_file:
                st.error("Please upload an excel file first")
            else:
                try:
                    # Create the directory
                    Path(migration_path).mkdir(parents=True, exist_ok=True)
                    
                    # Save the excel file
                    excel_path = os.path.join(migration_path, excel_file.name)
                    with open(excel_path, "wb") as f:
                        f.write(excel_file.getbuffer())
                    
                    st.success(f"✅ Folder created and file saved successfully!\n\nPath: {excel_path}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.markdown("---")

    # Information message
    st.info(
        """
        **Note:** Provide evidence of the Strategy validation/approval included in the Release 
        Migration via an email screen capture.
        """
    )
