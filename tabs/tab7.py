import streamlit as st
import os


def render_tab7() -> None:
    st.subheader("Portal Dashboard Migration – CLI Import")
    
    # Generate Commands button
    if st.button("Generate Commands", key="generate_cli_import_commands"):
        # Get data from session state
        site_name = st.session_state.get("site_name", "")
        env_server_path = st.session_state.get("env_server_path", "")
        
        # Validate inputs
        if not site_name:
            st.error("Please enter the site name in Setup Steps (Tab 1)")
        elif not env_server_path:
            st.error("Please enter the env server path in Import Files (Tab 5)")
        else:
            try:
                # Generate commands logic here
                commands = generate_cli_import_commands(site_name, env_server_path)
                st.session_state['cli_import_commands'] = commands
            except Exception as e:
                st.error(f"Error generating commands: {str(e)}")
    
    # Display commands text box
    if 'cli_import_commands' in st.session_state and st.session_state['cli_import_commands']:
        st.text_area(
            "Generated Commands:",
            value=st.session_state['cli_import_commands'],
            height=300,
            key="cli_import_commands_display"
        )
    
    # Instructions
    st.markdown("""
    ### Instructions:
    1. Navigate to `E:\\Applied Materials\\SmartFactoryRx_<Site>\\CLI\\bin` and open a CMD window.
    2. Click the **Generate commands** button and run each of them in the CMD one by one.
    """)


def generate_cli_import_commands(site_name: str, env_server_path: str) -> str:
    """Generate CLI import commands"""
    
    # Clean up the path
    env_server_path = env_server_path.strip().strip('"').strip("'")
    
    # Build the static file directory path
    static_file_directory = os.path.join(env_server_path, "Portal", "data", "static")
    
    # Build commands
    commands_list = []
    
    # Initial command
    commands_list.append(f"sfrxcli -i --env {site_name}")
    commands_list.append("")  # Empty line for readability
    
    # Import commands for each setting type
    setting_types = ["ProcessMap", "EquipmentHealth", "EquipmentView", "Operation"]
    
    for setting_type in setting_types:
        commands_list.append(f'ds --import --setting-type {setting_type} --static-file-directory "{static_file_directory}"')
    
    return '\n'.join(commands_list)
