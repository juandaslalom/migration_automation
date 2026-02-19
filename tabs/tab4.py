import streamlit as st
import os
import shutil
from pathlib import Path


def render_tab4() -> None:
    st.subheader("Folder Migration")

    def _get_base_path() -> str:
        """Resolve lower server base path (UNC)."""
        lower_base = st.session_state.get("lower_base_path", "").strip()
        if lower_base:
            return lower_base.rstrip("\\/")
        return ""
    
    st.markdown("""
    Insert all the paths of the folders to be migrated (located in the column others of the excel file)
    """)
    
    # Text area for folder paths
    folders_to_migrate = st.text_area(
        "Paths of the folders or files to move",
        height=200,
        key="folders_to_migrate",
        placeholder="Enter one path per line..."
    )
    
    st.markdown("---")
    
    # Copy folders button (centered)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📋 Copy Folders to Migration", type="primary", use_container_width=True):
            folders = st.session_state.get("folders_to_migrate", "")
            lower_base = st.session_state.get("lower_base_path", "").strip()
            release_name = st.session_state.get("release_name", "").strip()
            
            if not folders:
                st.error("Please enter the paths of folders to migrate")
            elif not lower_base or not release_name:
                st.error("Please complete the setup information in Tab 1 (lower server base path and release name)")
            else:
                # Build the migration path
                base_path = _get_base_path()
                if not base_path:
                    st.error("Please configure lower server base path in Tab 1")
                    st.stop()
                migration_path = os.path.join(base_path, "Applied Materials", "SmartFactoryRx_Westport", "Migration", release_name)
                try:
                    # Parse folder paths (one per line)
                    folder_list = [line.strip() for line in folders.split('\n') if line.strip()]
                    
                    # Strip quotes from paths
                    migration_path = migration_path.strip().strip('"').strip("'")
                    
                    # Create migration folder if it doesn't exist
                    Path(migration_path).mkdir(parents=True, exist_ok=True)
                    
                    results = []
                    errors = []
                    
                    # Create txt file with the paths in migration folder
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    txt_filename = f"migrated_paths_{timestamp}.txt"
                    txt_filepath = os.path.join(migration_path, txt_filename)
                    
                    with open(txt_filepath, 'w', encoding='utf-8') as f:
                        for path in folder_list:
                            f.write(f"{path}\n")
                    
                    for folder_path in folder_list:
                        try:
                            original_path = folder_path.strip().strip('"').strip("'")
                            
                            # Check if path exists
                            if not os.path.exists(original_path):
                                raise FileNotFoundError(f"Path does not exist: {original_path}")
                            
                            # Extract relative path structure
                            # Look for common base patterns like "SmartFactoryRx_" to preserve structure
                            if "SmartFactoryRx_" in original_path or "SmartFactory" in original_path:
                                # Find the part after SmartFactoryRx_SITE
                                parts = original_path.split(os.sep)
                                # Find index of folder containing "SmartFactoryRx"
                                sfrx_index = -1
                                for i, part in enumerate(parts):
                                    if "SmartFactoryRx" in part or "SmartFactory" in part:
                                        sfrx_index = i
                                        break
                                
                                if sfrx_index >= 0 and sfrx_index + 1 < len(parts):
                                    # Get relative path from after SmartFactoryRx_SITE folder
                                    relative_path = os.sep.join(parts[sfrx_index + 1:])
                                else:
                                    # Fallback: just use basename
                                    relative_path = os.path.basename(original_path.rstrip('/\\'))
                            else:
                                # For paths not containing SmartFactoryRx, just use basename
                                relative_path = os.path.basename(original_path.rstrip('/\\'))
                            
                            # Create destination with preserved structure
                            migration_dest = os.path.join(migration_path, relative_path)
                            
                            # Create parent directories if needed
                            os.makedirs(os.path.dirname(migration_dest), exist_ok=True)
                            
                            # Copy to migration folder
                            if os.path.isdir(original_path):
                                if os.path.exists(migration_dest):
                                    shutil.rmtree(migration_dest)
                                shutil.copytree(original_path, migration_dest)
                            else:
                                shutil.copy2(original_path, migration_dest)
                            
                            results.append(f"✓ {relative_path}")
                        except Exception as e:
                            errors.append(f"✗ {original_path}: {str(e)}")
                    
                    # Display results
                    if results:
                        st.success(f"✅ Migration completed!\n\nPaths saved to: {txt_filename}\n\n" + "\n".join(results))
                    if errors:
                        st.error("⚠️ Some items failed:\n\n" + "\n".join(errors))
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
