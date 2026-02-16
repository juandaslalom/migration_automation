import streamlit as st
import os
import subprocess
import time
from datetime import datetime


def render_tab7() -> None:
    st.subheader("Portal Dashboard Migration – CLI Import")
    
    # Generate Commands button
    if st.button("Generate Commands", key="generate_cli_import_commands"):
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
                commands = generate_cli_import_commands(site_name, release_name, migration_folder_path, equipments_file, equipments_text)
                st.session_state['cli_import_commands'] = commands
            except Exception as e:
                st.error(f"Error generating commands: {str(e)}")
    
    # Display commands text box
    if 'cli_import_commands' in st.session_state and st.session_state['cli_import_commands']:
        st.text_area(
            "Generated Commands:",
            value=st.session_state['cli_import_commands'],
            height=300,
            disabled=True,
            key="cli_import_commands_display"
        )
        
        st.markdown("---")
        
        # Test mode checkbox
        test_mode = st.checkbox("🧪 Test Mode (simulate CLI execution without sfrxcli)", value=False, key="cli_import_test_mode")
        
        if test_mode:
            st.info("ℹ️ Test mode enabled - will simulate CLI execution for testing purposes")
        
        # Run CLI Import Commands button (centered)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("▶️ Run CLI Import Commands", type="primary", use_container_width=True):
                try:
                    site_name = st.session_state.get("site_name", "")
                    release_name = st.session_state.get("release_name", "")
                    base_drive = st.session_state.get("base_drive", "").strip()
                    equipments_file = st.session_state.get("equipments_file")
                    equipments_text = st.session_state.get("equipments_text", "")
                    test_mode = st.session_state.get("cli_import_test_mode", False)
                    
                    # Build the migration path
                    base_path = base_drive + "\\" if not base_drive.endswith("\\") else base_drive
                    migration_folder_path = os.path.join(base_path, "Applied Materials", "SmartFactoryRx_Westport", "Migration", release_name)
                    
                    # Run the commands
                    with st.spinner("Running CLI import commands..." if not test_mode else "Simulating CLI import commands..."):
                        result = run_cli_import_commands(site_name, release_name, migration_folder_path, equipments_file, equipments_text, test_mode)
                    
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
    
    # Instructions - show dynamic path
    site_name = st.session_state.get("site_name", "")
    base_drive = st.session_state.get("base_drive", "E:")
    
    if site_name:
        cli_path = f"{base_drive}\\Applied Materials\\SmartFactoryRx_{site_name}\\CLI\\bin"
    else:
        cli_path = f"{base_drive}\\Applied Materials\\SmartFactoryRx_<Site>\\CLI\\bin"
    
    st.markdown(f"""
    ### Instructions:
    The commands will be automatically executed in the correct CLI directory (`{cli_path}`).
    
    1. Click **Generate Commands** to create the CLI import commands
    2. Review the generated commands
    3. Click **▶️ Run CLI Import Commands** to execute them automatically
    """)


def generate_cli_import_commands(site_name: str, release_name: str, migration_folder_path: str, equipments_file, equipments_text: str) -> str:
    """Generate CLI import commands for each equipment"""
    
    # Get equipments list
    equipments = []
    
    if equipments_file:
        # Read from uploaded file
        content = equipments_file.getvalue().decode("utf-8")
        equipments = [line.strip() for line in content.splitlines() if line.strip()]
    elif equipments_text:
        # Read from text input
        equipments = [line.strip() for line in equipments_text.splitlines() if line.strip()]
    
    # Build commands
    commands_list = []
    
    # Initial command
    commands_list.append(f"sfrxcli -i --env {site_name}")
    commands_list.append("")  # Empty line for readability
    
    # Generate commands for each equipment
    for equipment in equipments:
        # ie command for JSON file
        json_file = os.path.join(migration_folder_path, f"{release_name}-{equipment}.json")
        commands_list.append(f'ie -if "{json_file}" --comment "{release_name}"')
        
        # is command for CSV file
        csv_file = os.path.join(migration_folder_path, f"{release_name}-{equipment}.csv")
        commands_list.append(f'is -if "{csv_file}" --comment "{release_name}"')
        
        commands_list.append("")  # Empty line between equipment sets
    
    # Add exit command at the end
    commands_list.append("exit")
    
    return '\n'.join(commands_list)


def run_cli_import_commands(site_name: str, release_name: str, migration_folder_path: str, equipments_file, equipments_text: str, test_mode: bool = False) -> dict:
    """Run the CLI import commands"""
    
    try:
        # Create log file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = os.path.join(migration_folder_path, f"{release_name}_cli_import_log_{timestamp}.log")
        
        # Generate commands input (without the initial sfrxcli command)
        commands = generate_cli_import_commands(site_name, release_name, migration_folder_path, equipments_file, equipments_text)
        # Remove the first line (sfrxcli -i --env) as we'll execute it separately
        commands_input = '\n'.join(commands.split('\n')[2:])  # Skip first line and empty line
        
        # Prepare log content
        log_lines = []
        log_lines.append(f"=== CLI Import Commands Execution Log ===")
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
            json_pattern = r'ie -if ".*?-(.*?)\.json"'
            equipments = re.findall(json_pattern, commands_input)
            
            for equipment in equipments:
                simulated_output.append(f"Processing equipment: {equipment}")
                time.sleep(0.1)  # Small delay for realism
                simulated_output.append(f"  ✓ Importing equipment configuration from JSON... Done")
                simulated_output.append(f"  ✓ Importing equipment specs from CSV... Done")
                simulated_output.append(f"")
            
            simulated_output.append(f"All imports completed successfully!")
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
            # Build CLI bin directory path
            base_path = st.session_state.get("base_drive", "E:") + "\\"
            cli_bin_path = os.path.join(base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "CLI", "bin")
            
            # Check if CLI directory exists
            if not os.path.exists(cli_bin_path):
                error_msg = f"CLI directory not found: {cli_bin_path}"
                log_lines.append(f"\nERROR: {error_msg}")
                with open(log_file_path, 'w', encoding='utf-8') as log_file:
                    log_file.write('\n'.join(log_lines))
                return {
                    "success": False,
                    "output": "",
                    "error": error_msg,
                    "log_file": log_file_path
                }
            
            cli_command = f'sfrxcli -i --env {site_name}'
            
            log_lines.append(f"\nWorking directory: {cli_bin_path}")
            log_lines.append(f"Executing command: {cli_command}\n")
            log_lines.append(f"Commands to execute:\n{commands_input}\n")
            log_lines.append(f"=" * 50)
            log_lines.append(f"\nOutput:\n")
            
            # Run the command with stdin piping from the CLI bin directory
            process = subprocess.Popen(
                cli_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                cwd=cli_bin_path  # Set working directory to CLI bin
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
