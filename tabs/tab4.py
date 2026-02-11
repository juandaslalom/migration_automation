import streamlit as st
import os
import shutil
from pathlib import Path


def render_tab4() -> None:
    st.subheader("Folder Migration")
    
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
    
    st.markdown("Insert the path of the backup folder")
    
    # Text input for backup folder path
    backup_folder_path = st.text_input(
        "Paths of the backup folder",
        key="backup_folder_path",
        placeholder="E.g., /path/to/backup or C:\\path\\to\\backup"
    )
    
    st.markdown("---")
    
    # Copy folders and backup button (centered)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📋 Copy Folders and Backup", type="primary", use_container_width=True):
            folders = st.session_state.get("folders_to_migrate", "")
            backup_path = st.session_state.get("backup_folder_path", "")
            migration_path = st.session_state.get("migration_folder_path", "")
            
            if not folders:
                st.error("Please enter the paths of folders to migrate")
            elif not backup_path:
                st.error("Please enter the backup folder path")
            elif not migration_path:
                st.error("Please enter the migration folder path in Setup Steps (Tab 1)")
            else:
                try:
                    # Parse folder paths (one per line)
                    folder_list = [line.strip() for line in folders.split('\n') if line.strip()]
                    
                    # Create backup folder if it doesn't exist
                    Path(backup_path).mkdir(parents=True, exist_ok=True)
                    
                    # Create migration folder if it doesn't exist
                    Path(migration_path).mkdir(parents=True, exist_ok=True)
                    
                    results = []
                    errors = []
                    
                    for folder_path in folder_list:
                        try:
                            # Convert Windows absolute path to relative path if needed
                            original_path = folder_path
                            if folder_path.startswith('C:\\') or folder_path.startswith('c:\\'):
                                # Convert to relative path from workspace
                                folder_path = os.path.join(os.getcwd(), folder_path)
                            
                            # Check if path exists
                            if not os.path.exists(folder_path):
                                raise FileNotFoundError(f"Path does not exist: {original_path}")
                            
                            folder_name = os.path.basename(folder_path.rstrip('/\\'))
                            
                            # Copy to migration folder
                            migration_dest = os.path.join(migration_path, folder_name)
                            if os.path.isdir(folder_path):
                                shutil.copytree(folder_path, migration_dest, dirs_exist_ok=True)
                            else:
                                shutil.copy2(folder_path, migration_dest)
                            
                            # Copy to backup folder
                            backup_dest = os.path.join(backup_path, folder_name)
                            if os.path.isdir(folder_path):
                                shutil.copytree(folder_path, backup_dest, dirs_exist_ok=True)
                            else:
                                shutil.copy2(folder_path, backup_dest)
                            
                            results.append(f"✓ {folder_name}")
                        except Exception as e:
                            errors.append(f"✗ {folder_path}: {str(e)}")
                    
                    # Display results
                    if results:
                        st.success("✅ Migration and backup completed!\n\n" + "\n".join(results))
                    if errors:
                        st.error("⚠️ Some items failed:\n\n" + "\n".join(errors))
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
