import streamlit as st
import json
import os
import streamlit_authenticator as stauth

from tabs.tab1 import render_tab1
from tabs.tab2 import render_tab2
from tabs.tab3 import render_tab3
from tabs.tab4 import render_tab4
from tabs.tab5 import render_tab5
from tabs.tab6 import render_tab6
from tabs.tab7 import render_tab7
from tabs.tab8 import render_tab8
from tabs.tab9 import render_tab9
from tabs.tab10 import render_tab10

# Development mode settings file
DEV_SETTINGS_FILE = "dev_session_state.json"

def save_session_state():
    """Save current session state to file for development"""
    state_to_save = {}
    for key in st.session_state:
        # Only save simple types (strings, numbers, booleans)
        value = st.session_state[key]
        if isinstance(value, (str, int, float, bool)):
            state_to_save[key] = value
    
    with open(DEV_SETTINGS_FILE, 'w') as f:
        json.dump(state_to_save, f, indent=2)
    return True

def load_session_state():
    """Load session state from file for development"""
    if os.path.exists(DEV_SETTINGS_FILE):
        with open(DEV_SETTINGS_FILE, 'r') as f:
            saved_state = json.load(f)
        
        for key, value in saved_state.items():
            if key not in st.session_state:
                st.session_state[key] = value
        return True
    return False

# Auto-load session state on startup
if 'dev_state_loaded' not in st.session_state:
    load_session_state()
    st.session_state['dev_state_loaded'] = True

# Page configuration
st.set_page_config(
    page_title="Migration Automation",
    page_icon="🔄",
    layout="wide"
)

# Authentication using streamlit-authenticator
auth_config = st.secrets.get("auth", {})
users_cfg = auth_config.get("users", [])

if not users_cfg:
    st.error("Authentication is not configured. Add users under [auth] in .streamlit/secrets.toml.")
    st.stop()

# Build credentials dict expected by v0.4.x
credentials = {"usernames": {}}
for u in users_cfg:
    credentials["usernames"][u["username"]] = {
        "name": u.get("name", u["username"]),
        "password": u["password"],
    }

authenticator = stauth.Authenticate(
    credentials,
    auth_config.get("cookie_name", "sfrx_auth"),
    auth_config.get("cookie_key", "change_me"),
    auth_config.get("cookie_expiry_days", 7),
)

if st.session_state.get("authentication_status") is not True:
    authenticator.login()
    if st.session_state.get("authentication_status") is False:
        st.error("Invalid credentials")
    elif st.session_state.get("authentication_status") is None:
        st.warning("Please enter your credentials")
    st.stop()

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

# Development tools (in sidebar)
with st.sidebar:
    st.markdown("### 👤 Session")
    st.caption(f"Signed in as {st.session_state.get('name', '')}")
    authenticator.logout("Logout", "sidebar")
    st.markdown("---")
    st.markdown("### 🛠️ Dev Tools")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save State", use_container_width=True):
            if save_session_state():
                st.success("Saved!")
    with col2:
        if st.button("📂 Load State", use_container_width=True):
            if load_session_state():
                st.success("Loaded!")
                st.rerun()
            else:
                st.warning("No saved state found")
    
    if os.path.exists(DEV_SETTINGS_FILE):
        st.caption(f"✓ State file exists")
    
    st.markdown("---")

# Create tabs for Setup Steps
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(["1. Setup Steps", "2. E3 Export", "3. CLI Export", "4. Folder Migration", "5. Import Files", "6. E3 Import", "7. CLI Import", "8. Dashboard CLI Import", "9. Guardbands Import", "10. Service Restarts"])

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

with tab6:
    render_tab6()

with tab7:
    render_tab7()

with tab8:
    render_tab8()

with tab9:
    render_tab9()

with tab10:
    render_tab10()
