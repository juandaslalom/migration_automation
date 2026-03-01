import streamlit as st
import os
import subprocess


def render_tab4() -> None:
    st.subheader("Folder Migration")

    st.markdown("""
    Insert all the paths of the folders to be migrated (located in the column **others** of the excel file).

    Paths should be **local to the lower server** (e.g. `E:\\Applied Materials\\SmartFactoryRx_Westport\\Portal\\data\\static\\Equipment\\Lyophiliser1_Development`).

    The copy will run **on the lower server** via PowerShell Remoting.
    """)

    # Text area for folder paths
    folders_to_migrate = st.text_area(
        "Paths of the folders or files to move",
        height=200,
        key="folders_to_migrate",
        placeholder="E:\\Applied Materials\\SmartFactoryRx_Westport\\Portal\\data\\static\\Equipment\\Lyophiliser1_Development\nE:\\Applied Materials\\SmartFactoryRx_Westport\\Portal\\data\\static\\Equipment\\Lyophiliser2_Development"
    )

    # Test mode
    test_mode = st.checkbox("🧪 Test Mode (simulate copy without executing)", value=False, key="tab4_test_mode")
    if test_mode:
        st.info("ℹ️ Test mode enabled — will show the commands that would run but will NOT copy any files.")

    st.markdown("---")

    # Copy folders button (centered)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📋 Copy Folders to Migration", type="primary", use_container_width=True):
            folders = st.session_state.get("folders_to_migrate", "")
            lower_base = st.session_state.get("lower_base_path", "").strip()
            release_name = st.session_state.get("release_name", "").strip()
            site_name = st.session_state.get("site_name", "").strip()

            # --- Validate inputs ---
            if not folders:
                st.error("Please enter the paths of folders to migrate")
                st.stop()
            if not lower_base or not release_name or not site_name:
                st.error("Please complete the setup information in Tab 1 (lower server, site name, and release name)")
                st.stop()

            # --- Derive lower hostname from UNC base path (e.g. \\WA02835D\e$) ---
            lower_hostname = None
            try:
                parts = lower_base.lstrip("\\").split("\\")
                lower_hostname = parts[0] if parts else None
            except Exception:
                lower_hostname = None

            if not lower_hostname:
                st.error("Could not determine lower server hostname from base path. Check Tab 1 settings.")
                st.stop()

            # --- Build remote migration path (local to the lower server) ---
            remote_migration_path = os.path.join(
                "E:\\", "Applied Materials", f"SmartFactoryRx_{site_name}", "Migration", release_name
            )

            # Parse folder list
            folder_list = [line.strip().strip('"').strip("'") for line in folders.split('\n') if line.strip()]

            if not folder_list:
                st.error("No valid paths found.")
                st.stop()

            # --- Build the PowerShell script that will run on the lower server ---
            # The script will:
            #   1. Create the migration folder if it doesn't exist
            #   2. Save a log of source paths
            #   3. Copy each source into the migration folder preserving relative structure
            ps_lines = []
            ps_lines.append(f"$migrationPath = '{remote_migration_path}'")
            ps_lines.append("if (-not (Test-Path $migrationPath)) { New-Item -ItemType Directory -Path $migrationPath -Force | Out-Null }")
            ps_lines.append("")
            ps_lines.append("# Log file with source paths")
            ps_lines.append(f"$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'")
            ps_lines.append("$logFile = Join-Path $migrationPath \"migrated_paths_$timestamp.txt\"")
            ps_lines.append("")
            ps_lines.append("$results = @()")
            ps_lines.append("$errors = @()")
            ps_lines.append("$logEntries = @()")
            ps_lines.append("")

            for src_path in folder_list:
                # Compute relative path (after SmartFactoryRx_<Site>\)
                safe_src = src_path.replace("'", "''")
                ps_lines.append(f"# --- Process: {safe_src} ---")
                ps_lines.append(f"$src = '{safe_src}'")
                ps_lines.append("$logEntries += $src")
                ps_lines.append("if (Test-Path $src) {")
                # Extract relative path after SmartFactoryRx_*
                ps_lines.append("    $relPath = ''")
                ps_lines.append("    $idx = $src.IndexOf('SmartFactoryRx_')")
                ps_lines.append("    if ($idx -ge 0) {")
                ps_lines.append("        $afterSfrx = $src.Substring($idx)")
                ps_lines.append("        $sep = $afterSfrx.IndexOf('\\\\')")
                ps_lines.append("        if ($sep -lt 0) { $sep = $afterSfrx.IndexOf('\\') }")  # first backslash after SmartFactoryRx_SITE
                ps_lines.append("        if ($sep -ge 0) { $relPath = $afterSfrx.Substring($sep + 1) }")
                ps_lines.append("    }")
                ps_lines.append("    if ([string]::IsNullOrEmpty($relPath)) { $relPath = Split-Path $src -Leaf }")
                ps_lines.append("    $dst = Join-Path $migrationPath $relPath")
                ps_lines.append("    $dstParent = Split-Path $dst -Parent")
                ps_lines.append("    if (-not (Test-Path $dstParent)) { New-Item -ItemType Directory -Path $dstParent -Force | Out-Null }")
                ps_lines.append("    try {")
                ps_lines.append("        if (Test-Path $src -PathType Container) {")
                ps_lines.append("            if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }")
                ps_lines.append("            Copy-Item -Path $src -Destination $dst -Recurse -Force")
                ps_lines.append("        } else {")
                ps_lines.append("            Copy-Item -Path $src -Destination $dst -Force")
                ps_lines.append("        }")
                ps_lines.append("        $results += \"OK: $relPath\"")
                ps_lines.append("    } catch {")
                ps_lines.append("        $errors += \"FAIL: $src -> $($_.Exception.Message)\"")
                ps_lines.append("    }")
                ps_lines.append("} else {")
                ps_lines.append("    $errors += \"NOT_FOUND: $src\"")
                ps_lines.append("}")
                ps_lines.append("")

            # Write log file and output results
            ps_lines.append("# Save paths log")
            ps_lines.append("$logEntries | Out-File -FilePath $logFile -Encoding UTF8")
            ps_lines.append("")
            ps_lines.append("# Output summary")
            ps_lines.append("Write-Output '=== RESULTS ==='")
            ps_lines.append("$results | ForEach-Object { Write-Output $_ }")
            ps_lines.append("if ($errors.Count -gt 0) {")
            ps_lines.append("    Write-Output '=== ERRORS ==='")
            ps_lines.append("    $errors | ForEach-Object { Write-Output $_ }")
            ps_lines.append("}")

            remote_script = "\n".join(ps_lines)

            # --- Display generated script ---
            with st.expander("📝 View PowerShell script", expanded=False):
                st.code(remote_script, language="powershell")

            st.markdown(f"**Lower server:** `{lower_hostname}`  \n**Migration path:** `{remote_migration_path}`")

            if test_mode:
                st.warning("🧪 **Test Mode** — no files were copied. Review the script above.")
            else:
                # --- Execute via Invoke-Command on the lower server ---
                with st.spinner(f"Copying folders on {lower_hostname}..."):
                    try:
                        # Encode script as base64 to avoid quoting issues
                        import base64
                        script_bytes = remote_script.encode('utf-16-le')
                        script_b64 = base64.b64encode(script_bytes).decode('ascii')

                        ps_cmd = (
                            f"Invoke-Command -ComputerName {lower_hostname} "
                            f"-ScriptBlock {{ "
                            f"$script = [System.Text.Encoding]::Unicode.GetString("
                            f"[System.Convert]::FromBase64String('{script_b64}')); "
                            f"Invoke-Expression $script }}"
                        )

                        result = subprocess.run(
                            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                            capture_output=True,
                            text=True,
                            timeout=600,
                        )

                        output = result.stdout
                        if result.stderr:
                            output += f"\n\nSTDERR:\n{result.stderr}"

                        # Parse results
                        if "=== ERRORS ===" in output:
                            st.warning("⚠️ Some items failed:")
                            st.code(output, language="text")
                        elif "=== RESULTS ===" in output:
                            st.success("✅ Migration completed!")
                            st.code(output, language="text")
                        else:
                            st.info("Command completed. Output:")
                            st.code(output, language="text")

                    except subprocess.TimeoutExpired:
                        st.error("❌ Command timed out after 10 minutes.")
                    except Exception as e:
                        st.error(f"❌ Error executing remote copy: {str(e)}")
