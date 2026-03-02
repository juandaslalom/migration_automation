import streamlit as st
import os
from pathlib import Path


def render_tab1() -> None:
    # Input fields
    st.subheader("Setup Information")

    def _server_path(hostname: str) -> str:
        return f"\\\\{hostname}\\e$"

    SERVER_OPTIONS = [
        ("DEV App 1 - WA02835D (ABC, Sligo, Westport)", "WA02835D"),
        ("DEV App 2 - WA02836D (AP16, ABL, CampoC)", "WA02836D"),
        ("DEV App 3 - WA03144D (APL, ABS, LU)", "WA03144D"),
        ("DEV App 4 - WA02857D (Cork, AND)", "WA02857D"),
            ("QA App 1 - WA01928Q (ABC, Sligo, Westport)", "WA01928Q"),
        ("QA App 2 - WA01929Q (AP16, ABL, CampoC)", "WA01929Q"),
        ("QA App 3 - WA02101Q (APL, ABS, LU)", "WA02101Q"),
        ("QA App 4 - WA02102Q (Cork, AND)", "WA02102Q"),
        ("PROD App 1 - WA04756P (ABC, Sligo, Westport)", "WA04756P"),
        ("PROD App 2 - WA04757P (AP16, ABL, CampoC)", "WA04757P"),
        ("PROD App 3 - WA04862P (APL, ABS, LU)", "WA04862P"),
        ("PROD App 4 - WA04863P (Cork, AND)", "WA04863P"),
    ]

    st.segmented_control(
            "Select the site name",
        options=[
            "ABC",
            "Sligo",
            "Westport",
            "AP16",
            "ABL",
            "CampoC",
            "APL",
            "ABS",
            "LU",
            "Cork",
            "AND",
        ],
        key="site_name",
        selection_mode="single",
    )

    st.selectbox(
        "Select lower server",
        options=SERVER_OPTIONS,
        format_func=lambda opt: opt[0],
        key="lower_server_choice",
    )
    lower_hostname = st.session_state.get("lower_server_choice", SERVER_OPTIONS[0])[1]
    lower_base_path = _server_path(lower_hostname)
    st.session_state["lower_base_path"] = lower_base_path
    st.caption(f"Lower path: {lower_base_path}")

    st.selectbox(
        "Select upper server",
        options=SERVER_OPTIONS,
        format_func=lambda opt: opt[0],
        key="upper_server_choice",
    )
    upper_hostname = st.session_state.get("upper_server_choice", SERVER_OPTIONS[0])[1]
    upper_base_path = _server_path(upper_hostname)
    st.session_state["upper_base_path"] = upper_base_path
    st.caption(f"Upper path: {upper_base_path}")

    st.text_input(
        "Enter the release name (this will be the migration folder name)",
        placeholder="<Release Name>",
        key="release_name",
        help=r"Example: \\\\lower-server\\Applied Materials\\SmartFactoryRx_<Site>\\Migration\\<Release Name>"
    )

    st.markdown("---")

    # Remote credentials for PowerShell Remoting (Invoke-Command)
    st.subheader("Remote Credentials")
    st.markdown(
        "Used to connect to the selected servers via SMB (`net use`) and PowerShell Remoting. "
        "Entered once here and reused by tabs 3, 4, 7, and 8."
    )
    col_user, col_pass = st.columns(2)
    with col_user:
        st.text_input(
            "Remote Username",
            placeholder="DOMAIN\\\\username or username",
            key="remote_username",
        )
    with col_pass:
        st.text_input(
            "Remote Password",
            type="password",
            key="remote_password",
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
            site_name = (st.session_state.get("site_name") or "").strip()
            lower_base = (st.session_state.get("lower_base_path") or "").strip()
            release_name = (st.session_state.get("release_name") or "").strip()
            excel_file = st.session_state.get("excel_file")

            if not site_name:
                st.error("Please enter the site name")
            elif not lower_base:
                st.error("Please enter the lower server base path")
            elif not release_name:
                st.error("Please enter the release name")
            elif not excel_file:
                st.error("Please upload an excel file first")
            else:
                try:
                    # Build the migration path from the lower UNC base
                    base_path = lower_base.rstrip("\\/")
                    migration_path = os.path.join(base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "Migration", release_name)
                    
                    # Show the path that will be created
                    st.info(f"Creating folder at: {migration_path}")
                    
                    # Create the directory
                    Path(migration_path).mkdir(parents=True, exist_ok=True)
                    
                    # Verify the folder was created
                    if os.path.exists(migration_path):
                        st.success(f"✅ Folder created successfully at:\n{migration_path}")
                    
                    # Save the excel file into the migration folder
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
