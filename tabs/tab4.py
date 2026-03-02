import streamlit as st
import os
import shutil
import subprocess
from datetime import datetime


def _local_to_unc(local_path: str, hostname: str) -> str:
    """Convert a server-local path like E:\\foo\\bar to \\\\hostname\\e$\\foo\\bar"""
    p = local_path.strip().strip('"').strip("'")
    if len(p) >= 2 and p[1] == ':':
        drive = p[0].lower()
        rest = p[2:].lstrip('\\').lstrip('/')
        return f"\\\\{hostname}\\{drive}$\\{rest}"
    return p


def _get_rel_path(src_path: str) -> str:
    """Extract path relative to SmartFactoryRx_<site>\\ from a local server path."""
    idx = src_path.find('SmartFactoryRx_')
    if idx >= 0:
        after = src_path[idx:]
        sep = after.find('\\')
        if sep >= 0:
            return after[sep + 1:]
    return os.path.basename(src_path)


def render_tab4() -> None:
    st.subheader("Folder Migration")

    st.markdown("""
    Insert all the paths of the folders to be migrated (located in the column **others** of the excel file).

    Paths should be **local to the lower server** (e.g. `E:\\Applied Materials\\SmartFactoryRx_Westport\\Portal\\data\\static\\Equipment\\Lyophiliser1_Development`).

    The app will connect to the lower server over SMB using the credentials from Tab 1 and copy the files directly.
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
        st.info("ℹ️ Test mode enabled — will show what would be copied but will NOT copy any files.")

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📋 Copy Folders to Migration", type="primary", use_container_width=True):
            folders = st.session_state.get("folders_to_migrate", "")
            lower_base = (st.session_state.get("lower_base_path") or "").strip()
            release_name = (st.session_state.get("release_name") or "").strip()
            site_name = (st.session_state.get("site_name") or "").strip()
            remote_username = (st.session_state.get("remote_username") or "").strip()
            remote_password = st.session_state.get("remote_password", "")

            if not folders:
                st.error("Please enter the paths of folders to migrate")
                st.stop()
            if not lower_base or not release_name or not site_name:
                st.error("Please complete the setup information in Tab 1 (lower server, site name, and release name)")
                st.stop()
            if not remote_username or not remote_password:
                st.error("Please enter remote credentials in Tab 1 (Remote Credentials section)")
                st.stop()

            # Derive hostname from UNC base path (\\WA02835D\e$)
            try:
                lower_hostname = lower_base.lstrip("\\").split("\\")[0]
            except Exception:
                lower_hostname = None
            if not lower_hostname:
                st.error("Could not determine lower server hostname from base path. Check Tab 1 settings.")
                st.stop()

            # UNC share root and migration destination
            unc_share = f"\\\\{lower_hostname}\\e$"
            unc_migration_path = os.path.join(
                unc_share, "Applied Materials", f"SmartFactoryRx_{site_name}", "Migration", release_name
            )

            folder_list = [line.strip().strip('"').strip("'") for line in folders.split('\n') if line.strip()]
            if not folder_list:
                st.error("No valid paths found.")
                st.stop()

            # Build copy plan: (src_unc, dst_unc, rel)
            copy_plan = []
            for src_local in folder_list:
                rel = _get_rel_path(src_local)
                src_unc = _local_to_unc(src_local, lower_hostname)
                dst_unc = os.path.join(unc_migration_path, rel)
                copy_plan.append((src_unc, dst_unc, rel))

            with st.expander("📝 View copy plan", expanded=False):
                plan_text = "\n".join(f"{s}\n  → {d}" for s, d, _ in copy_plan)
                st.code(plan_text, language="text")

            st.markdown(f"**Lower server:** `{lower_hostname}`  \n**Migration path:** `{unc_migration_path}`")

            if test_mode:
                st.warning("🧪 **Test Mode** — no files were copied. Review the copy plan above.")
                st.stop()

            # Connect to the SMB share from the app host using supplied credentials
            with st.spinner(f"Connecting to {unc_share}..."):
                # Disconnect any stale connection first (ignore errors)
                subprocess.run(["net", "use", unc_share, "/delete", "/yes"],
                               capture_output=True, text=True)
                connect = subprocess.run(
                    ["net", "use", unc_share, f"/user:{remote_username}", remote_password],
                    capture_output=True, text=True
                )
                if connect.returncode != 0:
                    st.error(f"❌ Could not connect to {unc_share}:\n{connect.stderr or connect.stdout}")
                    st.stop()

            # Copy files over the UNC share
            results = []
            errors = []
            copied_local_paths = []
            with st.spinner("Copying files..."):
                try:
                    os.makedirs(unc_migration_path, exist_ok=True)
                except Exception as e:
                    subprocess.run(["net", "use", unc_share, "/delete", "/yes"], capture_output=True)
                    st.error(f"❌ Could not create migration folder: {e}")
                    st.stop()

                for src_local, (src_unc, dst_unc, rel) in zip(folder_list, copy_plan):
                    try:
                        if os.path.isdir(src_unc):
                            if os.path.exists(dst_unc):
                                shutil.rmtree(dst_unc)
                            shutil.copytree(src_unc, dst_unc)
                        elif os.path.isfile(src_unc):
                            os.makedirs(os.path.dirname(dst_unc), exist_ok=True)
                            shutil.copy2(src_unc, dst_unc)
                        else:
                            errors.append(f"NOT FOUND: {src_unc}")
                            continue
                        results.append(f"OK: {rel}")
                        copied_local_paths.append(src_local)
                    except Exception as e:
                        errors.append(f"FAIL: {rel} → {e}")

                # Write migrated_paths_*.txt so Tab 5 can read original source paths
                if copied_local_paths:
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        log_file = os.path.join(unc_migration_path, f"migrated_paths_{timestamp}.txt")
                        with open(log_file, "w", encoding="utf-8") as lf:
                            lf.write("\n".join(copied_local_paths))
                    except Exception as e:
                        errors.append(f"WARNING: Could not write migrated_paths log: {e}")
            # Disconnect the share
            subprocess.run(["net", "use", unc_share, "/delete", "/yes"], capture_output=True)

            summary = "\n".join(results + errors)
            if errors:
                st.warning("⚠️ Completed with errors:")
                st.code(summary, language="text")
            else:
                st.success("✅ Migration completed!")
                st.code(summary, language="text")
