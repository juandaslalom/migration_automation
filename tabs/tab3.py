import streamlit as st
import os
import subprocess
from pathlib import Path


def _unc_to_local(p: str) -> str:
    """Convert a UNC path (\\\\host\\share$\\rest) to a local drive path (X:\\rest)."""
    if p.startswith('\\\\'):
        try:
            parts = p.lstrip('\\').split('\\')
            if len(parts) >= 2:
                drive = parts[1][0].upper() + ':'
                rest = parts[2:]
                return os.path.join(drive + '\\', *rest) if rest else drive + '\\'
        except Exception:
            pass
    return p


def _host_from_unc(p: str) -> str:
    """Extract the hostname from a UNC path (\\\\hostname\\share$\\...)."""
    try:
        return p.lstrip('\\').split('\\')[0]
    except Exception:
        return ""


def render_tab3() -> None:
    st.subheader("CLI Export")

    st.info("CLI export will run using the lower server selection from Tab 1.")

    # Instructions and effective CLI path (shown upfront)
    site_name = st.session_state.get("site_name", "")
    lower_base = st.session_state.get("lower_base_path", "").strip()
    base_for_display = lower_base if lower_base else r"\\<lower-server>\share$"

    if site_name:
        cli_path = f"{base_for_display}\\Applied Materials\\SmartFactoryRx_{site_name}\\CLI\\bin"
    else:
        cli_path = f"{base_for_display}\\Applied Materials\\SmartFactoryRx_<Site>\\CLI\\bin"

    st.markdown(
        f"""
        ### Instructions
        Commands will run in `{cli_path}` automatically.

        1. Click **Generate Commands** to create the CLI export commands.
        2. Review the generated commands.
        3. Click **▶️ Run CLI Commands** to execute them automatically.
        """
    )

    def _get_lower_base_path() -> str:
        """Resolve lower server base path (UNC)."""
        lower_base = st.session_state.get("lower_base_path", "").strip()
        if not lower_base:
            return ""
        return lower_base.rstrip("\\/")
    
    # Generate Commands button
    if st.button("Generate Commands", key="generate_cli_commands"):
        # Get data from session state
        site_name = st.session_state.get("site_name", "")
        release_name = st.session_state.get("release_name", "")
        lower_base = st.session_state.get("lower_base_path", "").strip()
        equipments_file = st.session_state.get("equipments_file")
        equipments_text = st.session_state.get("equipments_text", "")
        
        # Validate inputs
        if not site_name:
            st.error("Please enter the site name in Setup Steps (Tab 1)")
        elif not release_name:
            st.error("Please enter the release name in Setup Steps (Tab 1)")
        elif not lower_base:
            st.error("Please enter the lower server base path in Setup Steps (Tab 1)")
        elif not equipments_file and not equipments_text:
            st.error("Please upload the equipments file or enter equipment names in Setup Steps (Tab 1)")
        else:
            try:
                # Build the migration path
                base_path = _get_lower_base_path()
                migration_folder_path = os.path.join(base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "Migration", release_name)
                
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
            disabled=True,
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
                    lower_base = st.session_state.get("lower_base_path", "").strip()
                    equipments_file = st.session_state.get("equipments_file")
                    equipments_text = st.session_state.get("equipments_text", "")
                    test_mode = st.session_state.get("cli_test_mode", False)
                    
                    # Build the migration path
                    base_path = _get_lower_base_path()
                    if not base_path:
                        st.error("Please enter the lower server base path in Setup Steps (Tab 1)")
                        st.stop()
                    migration_folder_path = os.path.join(base_path, "Applied Materials", f"SmartFactoryRx_{site_name}", "Migration", release_name)
                    
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
    


def generate_cli_commands(site_name: str, release_name: str, migration_folder_path: str, equipments_file, equipments_text: str) -> str:
    """Generate a preview of the actual Invoke-Command script that will run on the remote host."""

    # Read equipments
    if equipments_file:
        equipments_file.seek(0)
        content = equipments_file.read().decode('utf-8')
        equipments = [line.strip() for line in content.split('\n') if line.strip()]
    else:
        equipments = [line.strip() for line in equipments_text.split('\n') if line.strip()]

    # Derive remote host and local CLI bin path from the migration folder UNC
    remote_host = _host_from_unc(migration_folder_path)
    cli_bin_local = _unc_to_local(
        os.path.join(
            os.path.dirname(os.path.dirname(migration_folder_path)),  # up 2 from Migration/release
            f"SmartFactoryRx_{site_name}", "CLI", "bin"
        )
    )
    # Use UNC base to build CLI bin path correctly
    lower_base = st.session_state.get("lower_base_path", "").strip().rstrip("\\")
    cli_bin_unc = os.path.join(lower_base, "Applied Materials", f"SmartFactoryRx_{site_name}", "CLI", "bin")
    cli_bin_local = _unc_to_local(cli_bin_unc)
    remote_exe = os.path.join(cli_bin_local, "sfrxcli.exe")

    lines = []
    lines.append(f"# Runs on: {remote_host} via Invoke-Command")
    lines.append(f"cd '{cli_bin_local}'")
    lines.append("")

    for equipment in equipments:
        json_file = os.path.join(migration_folder_path, f"{release_name}-{equipment}.json")
        local_json = _unc_to_local(json_file)
        csv_file = os.path.join(migration_folder_path, f"{release_name}-{equipment}.csv")
        local_csv = _unc_to_local(csv_file)

        lines.append(f"& '{remote_exe}' ee -f '{local_json}' -e {equipment} --env {site_name}")
        lines.append(f"& '{remote_exe}' es -f '{local_csv}' -e {equipment} --env {site_name}")
        lines.append("")

    return '\n'.join(lines)


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
            # Build CLI bin directory path (lower server base path)
            base_override = st.session_state.get("lower_base_path", "").strip()
            if base_override:
                base_path = base_override.rstrip("\\/")
            else:
                return {
                    "success": False,
                    "output": "",
                    "error": "Lower server base path is required in Setup (Tab 1)",
                    "log_file": log_file_path
                }
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
            
            cli_command = f'"{os.path.join(cli_bin_path, "sfrxcli.exe")}" -i --env {site_name}'

            log_lines.append(f"\nCLI bin directory: {cli_bin_path}")
            log_lines.append(f"Executing command: {cli_command}\n")
            log_lines.append(f"Commands to execute:\n{commands_input}\n")
            log_lines.append(f"=" * 50)
            log_lines.append(f"\nOutput:\n")

            # Execute the CLI on the remote host via PowerShell Remoting (Invoke-Command).
            # Build a ScriptBlock that changes to the CLI bin directory on the remote host and
            # invokes `sfrxcli.exe` for each generated subcommand in non-interactive mode.
            try:
                # Derive remote host from the UNC base path (e.g. \\wa02835d\e$...)
                remote_host = None
                try:
                    parts = base_path.lstrip('\\').split('\\')
                    remote_host = parts[0] if parts else None
                except Exception:
                    remote_host = None

                if not remote_host:
                    raise RuntimeError("Could not determine remote host from base path")


                cli_bin_local = _unc_to_local(cli_bin_path)
                remote_exe = os.path.join(cli_bin_local, "sfrxcli.exe")

                # Build invocation lines: for each command like 'ee -f "..." -e X' produce
                # & 'E:\...\sfrxcli.exe' ee -f '...' -e X --env Westport
                cmd_lines = [ln.strip() for ln in commands_input.splitlines() if ln.strip() and ln.strip().lower() != 'exit']
                invocations = []
                for ln in cmd_lines:
                    # Escape single quotes for PowerShell single-quoted strings
                    safe_exe = remote_exe.replace("'", "''")
                    invocations.append(f"& '{safe_exe}' {ln} --env {site_name}")

                # Create the remote script: change directory then run each invocation separated by semicolons
                safe_cli_bin = cli_bin_local.replace("'", "''")
                remote_script = f"cd '{safe_cli_bin}'; {'; '.join(invocations)}"

                ps_cmd = f"Invoke-Command -ComputerName {remote_host} -ScriptBlock {{ {remote_script} }}"

                # Execute PowerShell and capture output
                ps_process = subprocess.run([
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    ps_cmd
                ], capture_output=True, text=True, timeout=900)

                full_output = ps_process.stdout
                if ps_process.stderr:
                    full_output += f"\n\nERRORS:\n{ps_process.stderr}"

                log_lines.append(full_output)
                log_lines.append(f"\n{'=' * 50}")
                returncode = ps_process.returncode

            except Exception as e_remote:
                # If remote execution fails, fall back to local execution (previous behavior)
                log_lines.append(f"\n[WARN] Remote execution failed: {str(e_remote)}. Falling back to local execution.")
                local_cwd = os.environ.get("SYSTEMROOT", r"E:\\Windows")
                process = subprocess.Popen(
                    cli_command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=True,
                    cwd=local_cwd
                )

                # Send commands to stdin
                stdout, stderr = process.communicate(input=commands_input, timeout=300)  # 5 min timeout
                full_output = stdout
                if stderr:
                    full_output += f"\n\nERRORS:\n{stderr}"

                # Add output to log
                log_lines.append(full_output)
                log_lines.append(f"\n{'=' * 50}")
                returncode = process.returncode

            # Unified post-execution logging and return
            log_lines.append(f"Exit code: {returncode}")
            log_lines.append(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Write log file
            log_content = '\n'.join(log_lines)
            with open(log_file_path, 'w', encoding='utf-8') as log_file:
                log_file.write(log_content)
            
            if returncode == 0:
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
                    "error": "Command failed with non-zero exit code",
                    "log_file": log_file_path
                }
            
    except subprocess.TimeoutExpired:
        error_msg = "Command execution timed out"
        try:
            process.kill()
        except Exception:
            pass
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
