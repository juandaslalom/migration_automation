import streamlit as st
import os


def render_tab3() -> None:
    st.subheader("CLI Export")
    
    # Generate Commands button
    if st.button("Generate Commands", key="generate_cli_commands"):
        # Get data from session state
        site_name = st.session_state.get("site_name", "")
        release_name = st.session_state.get("release_name", "")
        migration_folder_path = st.session_state.get("migration_folder_path", "")
        equipments_file = st.session_state.get("equipments_file")
        
        # Validate inputs
        if not site_name:
            st.error("Please enter the site name in Setup Steps (Tab 1)")
        elif not release_name:
            st.error("Please enter the release name in Setup Steps (Tab 1)")
        elif not migration_folder_path:
            st.error("Please enter the migration folder path in Setup Steps (Tab 1)")
        elif not equipments_file:
            st.error("Please upload the equipments file in Setup Steps (Tab 1)")
        else:
            try:
                # Generate commands logic here
                commands = generate_cli_commands(site_name, release_name, migration_folder_path, equipments_file)
                st.session_state['cli_commands'] = commands
            except Exception as e:
                st.error(f"Error generating commands: {str(e)}")
    
    # Display commands text box
    if 'cli_commands' in st.session_state and st.session_state['cli_commands']:
        st.text_area(
            "Generated Commands:",
            value=st.session_state['cli_commands'],
            height=300,
            key="cli_commands_display"
        )
    
    # Instructions
    st.markdown("""
    ### Instructions:
    1. Navigate to `E:\\Applied Materials\\SmartFactory\\Rx_<Site>\\CLI\\bin` and open a CMD window.
    2. Click the **Generate commands** button and run each of them in the CMD run them one by one.
    """)


def generate_cli_commands(site_name: str, release_name: str, migration_folder_path: str, equipments_file) -> str:
    """Generate CLI export commands based on equipments list"""
    
    # Read equipments from file
    equipments_file.seek(0)  # Reset file pointer
    content = equipments_file.read().decode('utf-8')
    equipments = [line.strip() for line in content.split('\n') if line.strip()]
    
    # Build commands
    commands_list = []
    
    # Static command
    commands_list.append(f"sfrxcli -i --env {site_name}")
    commands_list.append("")  # Empty line for readability
    
    # Dynamic commands for each equipment
    for equipment in equipments:
        # ee command
        json_file = os.path.join(migration_folder_path, f"{release_name}-{equipment}.json")
        commands_list.append(f'ee -f "{json_file}" -e {equipment}')
        
        # es command
        csv_file = os.path.join(migration_folder_path, f"{release_name}-{equipment}.csv")
        commands_list.append(f'es -f "{csv_file}" -e {equipment}')
        commands_list.append("")  # Empty line between equipment sets
    
    return '\n'.join(commands_list)
