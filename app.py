import streamlit as st

from tabs.tab1 import render_tab1
from tabs.tab2 import render_tab2
from tabs.tab3 import render_tab3
from tabs.tab4 import render_tab4
from tabs.tab5 import render_tab5

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
    </style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<div class="main-title">MIGRATION AUTOMATION</div>', unsafe_allow_html=True)

# Create tabs for Setup Steps
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Setup Steps", "E3 Export", "CLI Export", "Folder Migration", "TAB 5"])

with tab1:
    render_tab1()

with tab2:
    render_tab2()

with tab3:
    render_tab3()

with tab4:
    render_tab4()

with tab5:
    render_tab5()
