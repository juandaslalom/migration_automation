import streamlit as st


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
