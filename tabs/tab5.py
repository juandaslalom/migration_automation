import streamlit as st
import os
import shutil
from pathlib import Path
from datetime import datetime
import re


def render_tab5() -> None:
    st.subheader("Import Files")

    def _get_lower_base_path() -> str:
        lower_base = (st.session_state.get("lower_base_path") or "").strip()
        if lower_base:
            return lower_base.rstrip("\\/")
        return ""
    
    st.markdown("""
    **LOG IN TO THE UPPER SERVER**
    
    This tab is used after migration steps have been executed in the lower server.  
    Copy the migration folder from the lower server to the upper server, create backups, and transfer folders.
    """)
    
    st.markdown("---")
    
    # Path of the lower server (derived from Tab 1)
    st.markdown("**Path of the lower server**")

    site_name = (st.session_state.get("site_name") or "WESTPORT").strip()
    release_name = (st.session_state.get("release_name") or "").strip()
    lower_base = _get_lower_base_path()
    default_lower_path = ""

    if lower_base and release_name:
        default_lower_path = os.path.join(
            lower_base,
            "Applied Materials",
            f"SmartFactoryRx_{site_name}",
            "Migration",
            release_name,
        )

    if default_lower_path:
        st.info(
            f"Using lower server path from Tab 1 settings:\n\n`{default_lower_path}`\n\nUpdate Tab 1 if this looks incorrect."
        )
    else:
        st.warning("Lower server path is empty. Please fill site name, lower server base path, and release name in Tab 1.")

    st.session_state["lower_server_path"] = default_lower_path
    
    st.markdown("---")
    
    # Path of the upper server
    st.markdown("**Path of the upper server**")
    
    # Get site name from session state to build default path
    upper_base = (st.session_state.get("upper_base_path") or "").strip()
    base_for_env = upper_base if upper_base else "\\\\<upper-server>\\share$"
    default_env_path = f"{base_for_env}\\Applied Materials\\SmartFactoryRx_{site_name}"

    st.info(f"📍 Migration folder will be copied to:\n\n`{default_env_path}\\Migration`")

    st.session_state["env_server_path"] = default_env_path
    
    st.markdown("---")
    
    # Import button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📥 Import!", type="primary", use_container_width=True):
            lower_path = (st.session_state.get("lower_server_path") or "").strip().strip('"').strip("'")
            env_path = (st.session_state.get("env_server_path") or "").strip().strip('"').strip("'")
            
            if not lower_path:
                st.error("Lower server path is missing. Please update Tab 1 (site, lower base path, release name) or provide a custom lower path here.")
            elif not env_path:
                st.error("Please enter the path of the upper server")
            else:
                try:
                    # Check if lower server path exists
                    if not os.path.exists(lower_path):
                        st.error(f"Lower server path does not exist or is not reachable: {lower_path}")
                    else:
                        # Create Migration subfolder in env server path
                        migration_base_path = os.path.join(env_path, "Migration")
                        Path(migration_base_path).mkdir(parents=True, exist_ok=True)
                        
                        # Get migration folder name (last directory in the path)
                        migration_folder_name = os.path.basename(lower_path.rstrip('/\\'))
                        dest_migration_path = os.path.join(migration_base_path, migration_folder_name)
                        
                        # Copy the migration folder
                        with st.spinner(f"Importing {migration_folder_name}..."):
                            if os.path.exists(dest_migration_path):
                                shutil.rmtree(dest_migration_path)
                            shutil.copytree(lower_path, dest_migration_path)
                        
                        # Store in session state for later use
                        st.session_state["imported_migration_path"] = dest_migration_path
                        
                        st.success(f"✅ Migration folder imported successfully to:\n{dest_migration_path}")
                        
                except Exception as e:
                    st.error(f"Error during import: {str(e)}")
    
    st.markdown("---")
    
    # Check if import has been done
    import_done = "imported_migration_path" in st.session_state and st.session_state.get("imported_migration_path")
    
    # Check for data to backup button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 Check for data to backup", use_container_width=True, disabled=not import_done):
            env_path = (st.session_state.get("env_server_path") or "").strip().strip('"').strip("'")
            migration_path = st.session_state.get("imported_migration_path", "")
            
            if not migration_path:
                st.error("Please import the migration folder first")
            elif not os.path.exists(migration_path):
                st.error("Imported migration folder not found")
            else:
                try:
                    # Find the txt file with paths
                    txt_file = None
                    for file in os.listdir(migration_path):
                        if file.startswith("migrated_paths_") and file.endswith(".txt"):
                            txt_file = os.path.join(migration_path, file)
                            break
                    
                    if not txt_file:
                        # No log file — fall back to listing subfolders/files in the migration folder
                        st.warning("⚠️ No migrated_paths_*.txt found. Re-run Tab 4 to regenerate it. Falling back to scanning the migration folder structure.")
                        paths_from_txt = []
                        for item in os.listdir(migration_path):
                            full = os.path.join(migration_path, item)
                            if not item.endswith(".txt") and not item.endswith(".xlsx") and not item.endswith(".xls"):
                                paths_from_txt.append(full)
                    else:
                        # Read paths from txt file
                        with open(txt_file, 'r', encoding='utf-8') as f:
                            paths_from_txt = [line.strip() for line in f if line.strip()]

                    directories_needing_backup = []

                    # Process each path to find what already exists on the upper server
                    for original_path in paths_from_txt:
                        try:
                            parts = original_path.split('\\')

                            # Find where the meaningful relative path starts
                            meaningful_start = -1
                            for i, part in enumerate(parts):
                                if part in ['Portal', 'Guardbands', 'data', 'static']:
                                    meaningful_start = i
                                    break

                            if meaningful_start == -1:
                                for i, part in enumerate(parts):
                                    if 'SmartFactoryRx' in part:
                                        meaningful_start = i + 1
                                        break

                            if meaningful_start != -1:
                                rel_path = '\\'.join(parts[meaningful_start:])
                                target_path = os.path.join(env_path, rel_path)
                                if os.path.exists(target_path):
                                    directories_needing_backup.append(rel_path)

                        except Exception as e:
                            st.warning(f"Could not process path: {original_path} - {str(e)}")
                            continue

                    # Store in session state
                    st.session_state["directories_needing_backup"] = directories_needing_backup
                    st.session_state["env_base_path"] = env_path
                    st.session_state["txt_paths"] = paths_from_txt

                    if directories_needing_backup:
                        backup_text = "This directories need backup:\n" + "\n".join(directories_needing_backup)
                        st.session_state["backup_list_text"] = backup_text
                    else:
                        st.session_state["backup_list_text"] = "No directories need backup."
                        
                except Exception as e:
                    st.error(f"Error checking for backups: {str(e)}")
    
    # Display backup list
    if "backup_list_text" in st.session_state:
        st.text_area(
            "Directories requiring backup",
            value=st.session_state["backup_list_text"],
            height=200,
            disabled=True
        )
    
    st.markdown("---")
    
    # Create backups button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 Create backups", use_container_width=True, disabled=not import_done):
            directories_needing_backup = st.session_state.get("directories_needing_backup", [])
            env_base_path = st.session_state.get("env_base_path", "")
            migration_path = st.session_state.get("imported_migration_path", "")
            
            if not directories_needing_backup:
                st.warning("No directories need backup. Please check for data to backup first.")
            else:
                try:
                    # Extract date from migration folder name
                    migration_folder_name = os.path.basename(migration_path)
                    date_match = re.search(r'(\d{8})', migration_folder_name)
                    backup_date = date_match.group(1) if date_match else datetime.now().strftime("%Y%m%d")
                    backup_results = []
                    errors = []
                    
                    with st.spinner("Creating backups..."):
                        for rel_path in directories_needing_backup:
                            try:
                                target_path = os.path.join(env_base_path, rel_path)
                                backup_path = f"{target_path}-BKP-{backup_date}"

                                # Handle if backup already exists
                                counter = 2
                                original_backup_path = backup_path
                                while os.path.exists(backup_path):
                                    backup_path = f"{original_backup_path}-{counter}"
                                    counter += 1

                                # Rename to backup
                                os.rename(target_path, backup_path)
                                backup_results.append(f"{rel_path} → {backup_path}")

                            except Exception as e:
                                errors.append(f"{rel_path}: {str(e)}")

                    # Store backup results for transfer step
                    st.session_state["backup_results"] = backup_results

                    if backup_results:
                        st.success("✅ Backups created successfully:")
                        st.code("\n".join(backup_results), language="text")
                    if errors:
                        st.error("⚠️ Some backups failed:")
                        st.code("\n".join(errors), language="text")
                            
                except Exception as e:
                    st.error(f"Error creating backups: {str(e)}")
    
    st.markdown("---")
    
    # Transfer directories button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📦 Transfer directories", use_container_width=True, disabled=not import_done):
            migration_path = st.session_state.get("imported_migration_path", "")
            env_base_path = st.session_state.get("env_base_path", "")
            txt_paths = st.session_state.get("txt_paths", [])
            
            if not migration_path or not os.path.exists(migration_path):
                st.error("Please import the migration folder first")
            elif not txt_paths:
                st.error("Please check for data to backup first")
            else:
                try:
                    transferred = []
                    errors = []
                    
                    # Process each path from txt file
                    for original_path in txt_paths:
                        try:
                            # Extract the relative part after the base path
                            parts = original_path.split('\\')
                            
                            # Find where the meaningful path starts
                            meaningful_start = -1
                            for i, part in enumerate(parts):
                                if part in ['Portal', 'Guardbands', 'data', 'static']:
                                    meaningful_start = i
                                    break
                            
                            if meaningful_start == -1:
                                for i, part in enumerate(parts):
                                    if 'SmartFactoryRx' in part:
                                        meaningful_start = i + 1
                                        break
                            
                            if meaningful_start == -1:
                                errors.append(f"Could not process path: {original_path}")
                                continue
                            
                            # Get relative path
                            rel_path = '\\'.join(parts[meaningful_start:])
                            
                            # Find the folder in migration folder
                            # The folder name is the last part of the path
                            folder_name = parts[-1]
                            
                            # Search for this folder in migration folder
                            source_path = None
                            for root, dirs, files in os.walk(migration_path):
                                if folder_name in dirs:
                                    source_path = os.path.join(root, folder_name)
                                    break
                            
                            if not source_path:
                                errors.append(f"Folder not found in migration: {folder_name}")
                                continue
                            
                            # Build target path in env server
                            target_path = os.path.join(env_base_path, rel_path)
                            
                            # Show toast
                            st.toast(f"Moving {rel_path}...", icon="📦")
                            
                            # Create parent directories if needed
                            os.makedirs(os.path.dirname(target_path), exist_ok=True)
                            
                            # Copy the folder
                            if os.path.isdir(source_path):
                                shutil.copytree(source_path, target_path, dirs_exist_ok=True)
                            else:
                                shutil.copy2(source_path, target_path)
                            
                            transferred.append(f"{source_path} → {target_path}")
                            
                        except Exception as e:
                            errors.append(f"{original_path}: {str(e)}")
                    
                    if not errors:
                        st.success("✅ Transfer completed successfully!")
                    else:
                        st.warning("⚠️ Transfer completed with some errors")

                    if "backup_results" in st.session_state and st.session_state["backup_results"]:
                        st.markdown("**Directories renamed to backups:**")
                        st.code("\n".join(st.session_state["backup_results"]), language="text")

                    if transferred:
                        st.markdown("**Directories transferred:**")
                        st.code("\n".join(transferred), language="text")

                    if errors:
                        st.markdown("**Errors:**")
                        st.code("\n".join(errors), language="text")
                        
                except Exception as e:
                    st.error(f"Error during transfer: {str(e)}")
