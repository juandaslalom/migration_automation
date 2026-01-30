import streamlit as st
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Migration Automation",
    page_icon="🔄",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
        padding: 1rem;
        border: 3px solid #000;
        border-radius: 10px;
    }
    .section-box {
        border: 2px solid #000;
        border-radius: 10px;
        padding: 2rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<div class="main-title">MIGRATION AUTOMATION</div>', unsafe_allow_html=True)

# Create tabs for Setup Steps
tab1, tab2, tab3, tab4, tab5 = st.tabs(["TAB 1", "TAB 2", "TAB 3", "TAB 4", "TAB 5"])

with tab1:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    
    # Input fields
    st.subheader("Setup Information")
    
    site_name = st.text_input(
        "Enter the site name",
        placeholder="<Site Name>",
        key="site_name"
    )
    
    release_name = st.text_input(
        "Enter the release name",
        placeholder="<Release Name>",
        key="release_name"
    )
    
    migration_folder = st.text_input(
        "Enter the name of the migration folder",
        placeholder="<Migration Folder>",
        key="migration_folder"
    )
    
    migration_folder_path = st.text_input(
        "Enter the name of the migration folder path",
        value="E:\\Applied Materials\\SmartFactory/Rx_Westport\\Migration\\Westport_Eyecore-UPV8_Q4toProd_{YYYYMMDD}",
        key="migration_folder_path"
    )
    
    st.markdown("---")
    
    # File upload sections
    st.subheader("File Uploads")
    
    col1, col2 = st.columns(2)
    
    with col1:
        excel_file = st.file_uploader(
            "Upload your excel file",
            type=['xlsx', 'xls'],
            key="excel_file"
        )
        if excel_file:
            st.success(f"✓ {excel_file.name} uploaded successfully")
    
    with col2:
        equipments_file = st.file_uploader(
            "Upload your equipments file",
            type=['xlsx', 'xls', 'csv'],
            key="equipments_file"
        )
        if equipments_file:
            st.success(f"✓ {equipments_file.name} uploaded successfully")
    
    st.markdown("---")
    
    # Information message
    st.info("""
    **Note:** Provide evidence of the Strategy validation/approval included in the Release 
    Migration via an email screen capture.
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.write("Content for TAB 2")
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.write("Content for TAB 3")
    st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.write("Content for TAB 4")
    st.markdown('</div>', unsafe_allow_html=True)

with tab5:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.write("Content for TAB 5")
    st.markdown('</div>', unsafe_allow_html=True)
