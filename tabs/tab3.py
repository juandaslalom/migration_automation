import streamlit as st
import os
import subprocess
import tempfile
from pathlib import Path


def render_tab3() -> None:
    st.subheader("CLI Export")
    
    # Generate Commands button
    if st.button("Generate Commands", key="generate_cli_commands"):
        # Get data from session state
        site_name = st.session_state.get("site_name", "")
        release_name = st.session_state.get("release_name", "")
        base_drive = st.session_state.get("base_drive", "").strip()
        equipments_file = st.session_state.get("equipments_file")
        equipments_text = st.session_state.get("equipments_text", "")
        
        # Validate inputs
        if not site_name:
            st.error("Please enter the site name in Setup Steps (Tab 1)")
        elif not release_name:
            st.error("Please enter the release name in Setup Steps (Tab 1)")
        elif not base_drive:
            st.error("Please select the base drive in Setup Steps (Tab 1)")
        elif not equipments_file and not equipments_text:
            st.error("Please upload the equipments file or enter equipment names in Setup Steps (Tab 1)")
        else:
            try:
                # Build the migration path
                base_path = base_drive + "\\" if not base_drive.endswith("\\") else base_drive
                migration_folder_path = os.path.join(base_path, "Applied Materials", "SmartFactoryRx_Westport", "Migration", release_name)
                
                # Generate commands logic here
                commands = generate_cli_commands(site_name, release_name, migration_folder_path, equipments_file, equipments_text)
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
        
        st.markdown("---")
        
        # Test mode checkbox
        test_mode = st.checkbox("🧪 Test Mode (simulate CLI execution without sfrxcli)", value=False, key="cli_test_mode")
        
        if test_mode:
            st.info("ℹ️ Test mode enabled - will simulate CLI execution for testing purposes")
        
        # Run CLI Commands button (centered)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("▶️ Run CLI Commands", type="primary", use_container_width=True):
                try:
                    site_name = st.session_state.get("site_name", "")
                    release_name = st.session_state.get("release_name", "")
                    base_drive = st.session_state.get("base_drive", "").strip()
                    equipments_file = st.session_state.get("equipments_file")
                    equipments_text = st.session_state.get("equipments_text", "")
                    test_mode = st.session_state.get("cli_test_mode", False)
                    
                    # Build the migration path
                    base_path = base_drive + "\\" if not base_drive.endswith("\\") else base_drive
                    migration_folder_path = os.path.join(base_path, "Applied Materials", "SmartFactoryRx_Westport", "Migration", release_name)
                    
                    # Run the commands (cmd file is created and deleted automatically)
                    with st.spinner("Running CLI commands..." if not test_mode else "Simulating CLI commands..."):
                        result = run_cli_commands(site_name, release_name, migration_folder_path, equipments_file, equipments_text, test_mode)
                    
                    if result["success"]:
                        st.success(f"✅ Commands executed successfully!\n\nLog file: {result['log_file']}")
                    else:
                        st.error(f"❌ Error: {result['error']}")
                    
                    # Always show output in terminal-like interface
                    if result["output"]:
                        st.markdown("### 💻 Command Output")
                        st.code(result["output"], language="bash")
                    
                except Exception as e:
                    st.error(f"Error running commands: {str(e)}")
    
    # Instructions
    st.markdown("""
    ### Instructions:
    1. Navigate to `E:\\Applied Materials\\SmartFactory\\Rx_<Site>\\CLI\\bin` and open a CMD window.
    2. Click the **Generate commands** button and run each of them in the CMD run them one by one.
    """)


def generate_cli_commands(site_name: str, release_name: str, migration_folder_path: str, equipments_file, equipments_text: str) -> str:
    """Generate CLI export commands based on equipments list"""
    
    # Read equipments from file or text input
    if equipments_file:
        equipments_file.seek(0)  # Reset file pointer
        content = equipments_file.read().decode('utf-8')
        equipments = [line.strip() for line in content.split('\n') if line.strip()]
    else:
        equipments = [line.strip() for line in equipments_text.split('\n') if line.strip()]
    
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


def create_cmd_file(site_name: str, release_name: str, migration_folder_path: str, equipments_file, equipments_text: str) -> str:
    """Create a temporary .cmd file with CLI commands (without sfrxcli -i line) for piping"""
    
    # Read equipments from file or text input
    if equipments_file:
        equipments_file.seek(0)  # Reset file pointer
        content = equipments_file.read().decode('utf-8')
        equipments = [line.strip() for line in content.split('\n') if line.strip()]
    else:
        equipments = [line.strip() for line in equipments_text.split('\n') if line.strip()]
    
    # Build commands (WITHOUT sfrxcli -i line - those will be piped into it)
    commands_list = []
    
    # Dynamic commands for each equipment
    for equipment in equipments:
        # ee command
        json_file = os.path.join(migration_folder_path, f"{release_name}-{equipment}.json")
        commands_list.append(f'ee -f "{json_file}" -e {equipment}')
        
        # es command
        csv_file = os.path.join(migration_folder_path, f"{release_name}-{equipment}.csv")
        commands_list.append(f'es -f "{csv_file}" -e {equipment}')
    
    # Add exit command at the end
    commands_list.append("exit")
    
    # Return the commands as a string (not saving to file)
    return '\n'.join(commands_list)


def run_cli_commands(site_name: str, release_name: str, migration_folder_path: str, equipments_file, equipments_text: str, test_mode: bool = False) -> dict:
    """Run the CLI commands using a temporary .cmd file"""
    
    from datetime import datetime
    import time
    
    try:
        # Create log file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = os.path.join(migration_folder_path, f"{release_name}_cli_export_log_{timestamp}.log")
        
        # Generate commands content
        commands_input = create_cmd_file(site_name, release_name, migration_folder_path, equipments_file, equipments_text)
        
        # Prepare log content
        log_lines = []
        log_lines.append(f"=== CLI Export Commands Execution Log ===")
        log_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_lines.append(f"Site: {site_name}")
        log_lines.append(f"Release: {release_name}")
        log_lines.append(f"Mode: {'TEST (Simulated)' if test_mode else 'PRODUCTION'}")
        log_lines.append(f"=" * 50)
        
        if test_mode:
            # SIMULATE CLI execution for testing
            log_lines.append(f"\n[TEST MODE] Simulating command: sfrxcli -i --env {site_name}\n")
            log_lines.append(f"Commands to execute:\n{commands_input}\n")
            log_lines.append(f"=" * 50)
            log_lines.append(f"\nSimulated Output:\n")
            
            # Generate fake but realistic output
            simulated_output = []
            simulated_output.append(f"SmartFactoryRx CLI v2.5.1")
            simulated_output.append(f"Connecting to environment: {site_name}...")
            simulated_output.append(f"Connected successfully to {site_name}")
            simulated_output.append(f"")
            
            # Read equipments from commands
            import re
            equipment_pattern = r'-e (\w+)'
            equipments = re.findall(equipment_pattern, commands_input)
            unique_equipments = list(dict.fromkeys(equipments))  # Remove duplicates while preserving order
            
            for equipment in unique_equipments:
                simulated_output.append(f"Processing equipment: {equipment}")
                time.sleep(0.1)  # Small delay for realism
                simulated_output.append(f"  ✓ Exporting equipment configuration to JSON... Done")
                simulated_output.append(f"  ✓ Exporting equipment specs to CSV... Done")
                simulated_output.append(f"")
            
            simulated_output.append(f"All exports completed successfully!")
            simulated_output.append(f"Session closed.")
            
            full_output = '\n'.join(simulated_output)
            log_lines.append(full_output)
            log_lines.append(f"\n{'=' * 50}")
            log_lines.append(f"[TEST MODE] Simulated exit code: 0")
            log_lines.append(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Write log file
            log_content = '\n'.join(log_lines)
            with open(log_file_path, 'w', encoding='utf-8') as log_file:
                log_file.write(log_content)
            
            return {
                "success": True, 
                "output": full_output, 
                "error": None,
                "log_file": log_file_path
            }
        
        else:
            # REAL CLI execution
            cli_command = f'sfrxcli -i --env {site_name}'
            
            log_lines.append(f"\nExecuting command: {cli_command}\n")
            log_lines.append(f"Commands to execute:\n{commands_input}\n")
            log_lines.append(f"=" * 50)
            log_lines.append(f"\nOutput:\n")
            
            # Run the command with stdin piping
            process = subprocess.Popen(
                cli_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            
            # Send commands to stdin
            stdout, stderr = process.communicate(input=commands_input, timeout=300)  # 5 min timeout
            
            # Combine stdout and stderr
            full_output = stdout
            if stderr:
                full_output += f"\n\nERRORS:\n{stderr}"
            
            # Add output to log
            log_lines.append(full_output)
            log_lines.append(f"\n{'=' * 50}")
            log_lines.append(f"Exit code: {process.returncode}")
            log_lines.append(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Write log file
            log_content = '\n'.join(log_lines)
            with open(log_file_path, 'w', encoding='utf-8') as log_file:
                log_file.write(log_content)
            
            if process.returncode == 0:
                return {
                    "success": True, 
                    "output": full_output, 
                    "error": None,
                    "log_file": log_file_path
                }
            else:
                return {
                    "success": False, 
                    "output": full_output, 
                    "error": stderr or "Command failed with non-zero exit code",
                    "log_file": log_file_path
                }
            
    except subprocess.TimeoutExpired:
        process.kill()
        error_msg = "Command execution timed out (5 minutes)"
        log_lines.append(f"\n\nERROR: {error_msg}")
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            log_file.write('\n'.join(log_lines))
        return {
            "success": False, 
            "output": '\n'.join(log_lines), 
            "error": error_msg,
            "log_file": log_file_path
        }
    except Exception as e:
        error_msg = str(e)
        log_lines.append(f"\n\nEXCEPTION: {error_msg}")
        try:
            with open(log_file_path, 'w', encoding='utf-8') as log_file:
                log_file.write('\n'.join(log_lines))
        except:
            pass
        return {
            "success": False, 
            "output": '\n'.join(log_lines), 
            "error": error_msg,
            "log_file": log_file_path if 'log_file_path' in locals() else "N/A"
        }
