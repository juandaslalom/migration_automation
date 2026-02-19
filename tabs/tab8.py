import streamlit as st
import os
import subprocess
from datetime import datetime


def render_tab8() -> None:
    st.subheader("Dashboard CLI Import")

    def _get_base_path() -> str:
        """Resolve base path using UNC override if provided, else drive letter."""
        override = st.session_state.get("base_path_override", "").strip()
        if override:
            return override.rstrip("\\/")
        base_drive_val = st.session_state.get("base_drive", "").strip()
        if base_drive_val:
            return base_drive_val if base_drive_val.endswith("\\") else base_drive_val + "\\"
        return ""
    
    # Generate Commands button
    if st.button("Generate Commands", key="generate_dashboard_cli_commands"):
        # Get data from session state
        site_name = st.session_state.get("site_name", "")
        base_drive = st.session_state.get("base_drive", "").strip()
        base_path_override = st.session_state.get("base_path_override", "").strip()
        
        # Validate inputs
        if not site_name:
            st.error("Please enter the site name in Setup Steps (Tab 1)")
        elif not (base_drive or base_path_override):
            st.error("Please select a base drive or enter a UNC base path in Setup Steps (Tab 1)")
        else:
            try:
                # Generate commands logic here
                base_root = _get_base_path()
                commands = generate_dashboard_cli_commands(site_name, base_root)
                st.session_state['dashboard_cli_commands'] = commands
            except Exception as e:
                st.error(f"Error generating commands: {str(e)}")
    
    # Display commands text box
    if 'dashboard_cli_commands' in st.session_state and st.session_state['dashboard_cli_commands']:
        st.text_area(
            "Generated Commands:",
            value=st.session_state['dashboard_cli_commands'],
            height=300,
            disabled=True,
            key="dashboard_cli_commands_display"
        )
        
        st.markdown("---")
        
        # Test mode checkbox
        test_mode = st.checkbox("🧪 Test Mode (simulate CLI execution without sfrxcli)", value=False, key="dashboard_cli_test_mode")
        
        if test_mode:
            st.info("ℹ️ Test mode enabled - will simulate CLI execution for testing purposes")
        else:
            # Credentials input (only in production mode)
            st.markdown("#### 🔐 CLI Credentials")
            st.info("Enter your SmartFactory Rx CLI credentials.")
            
            col_user, col_pass = st.columns(2)
            with col_user:
                cli_username = st.text_input("Username", key="dashboard_cli_username", autocomplete="off")
            with col_pass:
                cli_password = st.text_input("Password", type="password", key="dashboard_cli_password", autocomplete="off")
        
        # Run Dashboard CLI Commands button (centered)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("▶️ Run Dashboard CLI Commands", type="primary", use_container_width=True):
                try:
                    site_name = st.session_state.get("site_name", "")
                    base_drive = st.session_state.get("base_drive", "").strip()
                    base_path_override = st.session_state.get("base_path_override", "").strip()
                    test_mode = st.session_state.get("dashboard_cli_test_mode", False)
                    
                    # Get credentials (only in production mode)
                    cli_username = None
                    cli_password = None
                    if not test_mode:
                        cli_username = st.session_state.get("dashboard_cli_username", "")
                        cli_password = st.session_state.get("dashboard_cli_password", "")
                        
                        if not cli_username or not cli_password:
                            st.error("⚠️ Please enter both username and password")
                            st.stop()
                    
                    # Build the migration path for log file
                    base_root = _get_base_path()
                    if not base_root:
                        st.error("Please select a base drive or enter a UNC base path in Setup Steps (Tab 1)")
                        st.stop()
                    log_folder_path = os.path.join(base_root, "Applied Materials", "SmartFactoryRx_Westport", "Portal", "data", "static")
                    
                    # Run the commands
                    with st.spinner("Running Dashboard CLI commands..." if not test_mode else "Simulating Dashboard CLI commands..."):
                        result = run_dashboard_cli_commands(site_name, base_root, log_folder_path, test_mode, cli_username, cli_password)
                    
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
    base_path_override = st.session_state.get("base_path_override", "").strip()
    base_for_display = base_path_override if base_path_override else base_drive
    
    if site_name:
        cli_path = f"{base_for_display}\\Applied Materials\\SmartFactoryRx_{site_name}\\CLI\\bin"
    else:
        cli_path = f"{base_for_display}\\Applied Materials\\SmartFactoryRx_<Site>\\CLI\\bin"
    
    st.markdown(f"""
    ### Instructions:
    The commands will be automatically executed in the correct CLI directory (`{cli_path}`).
    
    1. Click **Generate Commands** to create the Dashboard CLI import commands
    2. Review the generated commands
    3. Click **▶️ Run Dashboard CLI Commands** to execute them automatically
    
    **Commands will import:**
    - Process Map domain settings
    - Equipment Health domain settings
    - Equipment View domain settings
    - Operation domain settings
    """)


def generate_dashboard_cli_commands(site_name: str, base_drive: str) -> str:
    """Generate Dashboard CLI import commands"""
    
    # Build the static file directory path
    if base_drive.startswith("\\"):
        base_path = base_drive.rstrip("\\/")
    else:
        base_path = base_drive if base_drive.endswith("\\") else base_drive + "\\"
    static_directory = os.path.join(base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "Portal", "data", "static")
    
    # Build commands
    commands_list = []
    
    # Initial command
    commands_list.append(f"sfrxcli -i --env {site_name}")
    commands_list.append("")  # Empty line for readability
    
    # Domain settings import commands
    setting_types = ["ProcessMap", "EquipmentHealth", "EquipmentView", "Operation"]
    
    for setting_type in setting_types:
        commands_list.append(f'ds --import --setting-type {setting_type} --static-file-directory "{static_directory}"')
        commands_list.append("")  # Empty line between commands
    
    # Add exit command at the end
    commands_list.append("exit")
    
    return '\n'.join(commands_list)


def run_dashboard_cli_commands(site_name: str, base_drive: str, log_folder_path: str, test_mode: bool = False, username: str = None, password: str = None) -> dict:
    """Run the Dashboard CLI import commands"""
    
    try:
        # Create log file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = os.path.join(log_folder_path, f"dashboard_cli_import_log_{timestamp}.log")
        
        # Generate commands input (without the initial sfrxcli command)
        commands = generate_dashboard_cli_commands(site_name, base_drive)
        # Remove the first line (sfrxcli -i --env) as we'll execute it separately
        commands_input = '\n'.join(commands.split('\n')[2:])  # Skip first line and empty line
        
        # Prepare log content
        log_lines = []
        log_lines.append(f"=== Dashboard CLI Import Commands Execution Log ===")
        log_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_lines.append(f"Site: {site_name}")
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
            
            setting_types = ["ProcessMap", "EquipmentHealth", "EquipmentView", "Operation"]
            
            for setting_type in setting_types:
                simulated_output.append(f"Importing domain settings: {setting_type}")
                simulated_output.append(f"  ✓ Reading configuration files... Done")
                simulated_output.append(f"  ✓ Validating data... Done")
                simulated_output.append(f"  ✓ Importing to database... Done")
                simulated_output.append(f"")
            
            simulated_output.append(f"All domain settings imported successfully!")
            simulated_output.append(f"Session closed.")
            
            full_output = '\n'.join(simulated_output)
            log_lines.append(full_output)
            log_lines.append(f"\n{'=' * 50}")
            log_lines.append(f"[TEST MODE] Simulated exit code: 0")
            log_lines.append(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Write log file
            log_content = '\n'.join(log_lines)
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
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
            if base_drive.startswith("\\"):
                base_path = base_drive.rstrip("\\/")
            else:
                base_path = base_drive if base_drive.endswith("\\") else base_drive + "\\"
            cli_bin_path = os.path.join(base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "CLI", "bin")
            
            # Check if CLI directory exists
            if not os.path.exists(cli_bin_path):
                error_msg = f"CLI directory not found: {cli_bin_path}"
                log_lines.append(f"\nERROR: {error_msg}")
                os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
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
            log_lines.append(f"User: {username}")
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
            
            # Prepare full input with credentials and commands
            # CLI will prompt for username and password first
            full_input = f"{username}\n{password}\n{commands_input}"
            
            # Send credentials and commands to stdin
            stdout, stderr = process.communicate(input=full_input, timeout=300)  # 5 min timeout
            
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
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
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
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
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
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
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
