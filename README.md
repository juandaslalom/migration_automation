# SmartFactory Rx Migration Automation Tool

A comprehensive Streamlit-based web application designed to automate and streamline the migration process for SmartFactory Rx environments. This tool guides users through the entire migration workflow from setup to execution, covering E3 exports/imports, CLI operations, folder management, and service restarts.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Features](#features)
- [Tab-by-Tab Guide](#tab-by-tab-guide)
- [Development Tools](#development-tools)
- [Troubleshooting](#troubleshooting)

## Overview

This application provides a user-friendly interface for managing SmartFactory Rx migration tasks across different environments (QA to Production). It automates repetitive tasks, reduces human error, and maintains consistency across migrations.

## Prerequisites

- **Python**: 3.8 or higher
- **Operating System**: Windows (required for service management features)
- **Access Requirements**:
  - Network access to SmartFactory Rx servers
  - Administrator privileges (for service restart functionality in Tab 6)
  - Optional: `sfrxcli` installed (for CLI export operations in Tab 3)
- **Authentication config**: `.streamlit/secrets.toml` with user credentials (see Authentication Setup)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/juandaslalom/migration_automation.git
cd migration_automation
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Authentication Setup

Create `.streamlit/secrets.toml` with cookie settings and user accounts (passwords should be hashed using `streamlit-authenticator`). Example:

```toml
[auth]
cookie_name = "sfrx_auth"
cookie_key = "change_this_key"
cookie_expiry_days = 7

[[auth.users]]
name = "Admin User"
username = "admin"
password = "$2b$12$...hashed password..."
```

Generate a hashed password (one time) in Python:

```python
import streamlit_authenticator as stauth

print(stauth.Hasher(["PlaintextPasswordHere"]).generate()[0])
```

## Running the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

The application will open automatically in your default browser at `http://localhost:8501`.

## Features

### Core Functionality
- **Multi-tab interface** with 9 specialized tabs for different migration phases
- **Session state management** with save/load functionality for development
- **Path auto-generation** based on site, drive, and release configurations
- **Test modes** available for CLI and service operations
- **Comprehensive error handling** with detailed feedback
- **Login protection** using `streamlit-authenticator`

### Tab 1: Setup Steps
- Configure site name, drive letter (C:/D:/E:), and release name
- Dual equipment input: file upload or manual text entry
- Excel file upload for migration documentation
- Automatic path generation for migration folders

### Tab 2: E3 Export
- E3 package (.e3pkg) file upload
- Automatic file placement in migration folder
- Path-based organization

### Tab 3: CLI Export
- Equipment-based CLI command generation for `sfrxcli`
- Command execution with stdin piping via `.cmd` files
- **Test Mode**: Simulate CLI operations without actual `sfrxcli` installation
- Log file generation with timestamps (`.log` format)
- Real-time execution feedback

### Tab 4: Folder Migration
- Copy source folders to migration directory
- **Path structure preservation** after `SmartFactoryRx_<Site>` folder
- Generate `migrated_paths_<timestamp>.txt` for tracking
- Visual progress feedback

### Tab 5: Import Files (ENV Server)
- Import migration folder from lower (QA) server to ENV server
- Auto-generate ENV server paths with custom override option
- **Check for data to backup**: Scan for existing directories
- **Create backups**: Rename existing folders with `-BKP-<date>` suffix
- **Transfer directories**: Copy from migration to ENV server
- Comprehensive transfer summary with full paths
- Sequential workflow with button dependencies

### Tab 6: E3 Import
- Step-by-step E3 import instructions
- **Automated service restart** functionality:
  - Individual restart: `SFRx_<Site>_E3Client` and `SFRx_<Site>_Portal`
  - Batch restart: Both services simultaneously
  - **7-second mandatory wait** between restart operations
  - **Test Mode**: Simulate service restarts without admin privileges
- Visual countdown timer for wait periods

### Tab 7: CLI Import
- CLI import command generation
- Instructions for manual execution

## Tab-by-Tab Guide

### Tab 1: Setup Steps ⚙️

1. **Select Drive**: Choose C:, D:, or E: from dropdown
2. **Enter Site Name**: e.g., "WESTPORT"
3. **Enter Release Name**: e.g., "Westport_Eyecare-UPV8_QAtoProd_20260130"
4. **Add Equipments**:
   - Option A: Upload `.txt` file with one equipment per line
   - Option B: Manually enter equipment names in text area
5. **Upload Excel File**: Upload migration documentation Excel file

**Output**: Migration path auto-generated as `{Drive}:\Applied Materials\SmartFactoryRx_{Site}\Migration\{Release}`

### Tab 2: E3 Export 📦

1. Ensure Tab 1 is completed
2. Upload `.e3pkg` file
3. File automatically saved to migration folder

### Tab 3: CLI Export 💻

1. Review generated CLI commands for each equipment
2. Click **Execute CLI Commands** to run export
3. **Test Mode Option**: Enable to simulate without `sfrxcli`
4. Monitor progress and view log file path
5. Check generated `.log` file for results

### Tab 4: Folder Migration 📂

1. Add folder paths to migrate (one per line)
2. Click **Copy to Migration Folder**
3. Folders copied while preserving structure
4. Review `migrated_paths_<timestamp>.txt` for tracking

### Tab 5: Import Files 🚀

**Important**: This tab is for ENV server operations (after QA migration is complete)

1. **Enter Lower Server Path**: Path to migration folder on QA server
2. **Verify ENV Path**: Auto-generated or provide custom path
3. Click **📥 Import!**: Copy migration folder to ENV server
4. Click **🔍 Check for data to backup**: Scan for existing directories
5. Review backup list
6. Click **💾 Create backups**: Rename existing folders with backup suffix
7. Click **📦 Transfer directories**: Copy new folders to ENV server
8. Review comprehensive transfer summary

### Tab 6: E3 Import ⚡

1. Follow manual E3 import instructions (steps 1-7)
2. **Service Restart (Step 8)**:
   - Enable **🧪 Test Mode** if no admin privileges (for testing)
   - Choose restart option:
     - **🔄 Restart E3Client Service**: Restart E3Client only
     - **🔄 Restart Portal Service**: Restart Portal only
     - **🔄 Restart Both Services**: Restart both simultaneously
   - Wait 7 seconds between operations (enforced automatically)

### Tab 7: CLI Import 📋

1. Review generated CLI import commands
2. Copy commands for manual execution

## Development Tools

### Session State Management

Located in the sidebar:
- **💾 Save State**: Save current session state to `dev_session_state.json`
- **📂 Load State**: Restore previously saved session state
- Useful for development and testing workflows
- Excludes widget keys (buttons, file uploaders) from persistence

## Troubleshooting

### "Could not find migrated_paths_*.txt file"
- Ensure you completed Tab 4 and generated the migration paths file
- In Tab 5, click **📥 Import!** button before other operations

### Service Restart Buttons Disabled
- In Tab 5: Complete the **📥 Import!** step first
- In Tab 6: Wait 7 seconds after previous restart operation

### "Access is denied" (Service Restart)
- Option 1: Run Streamlit as Administrator
- Option 2: Enable **🧪 Test Mode** to simulate without admin privileges

### CLI Commands Not Working
- Enable **Test Mode** in Tab 3 to verify UI without `sfrxcli`
- Ensure `sfrxcli` is installed and in system PATH for production use

### Path Issues
- Verify drive letter selection matches actual server drive
- Check that site name matches server naming convention
- Confirm release name follows required format

## Project Structure

```
migration_automation/
├── app.py                      # Main Streamlit application
├── tabs/
│   ├── __init__.py
│   ├── tab1.py                # Setup Steps
│   ├── tab2.py                # E3 Export
│   ├── tab3.py                # CLI Export
│   ├── tab4.py                # Folder Migration
│   ├── tab5.py                # Import Files
│   ├── tab6.py                # E3 Import (with service restart)
│   └── tab7.py                # CLI Import
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── create_test_services.ps1   # Create dummy services for testing
└── remove_test_services.ps1   # Remove dummy test services
```

## Contributing

This project is maintained by the migration automation team. For questions or issues, please contact the development team.

## Version History

- **v2.0** (2026-02-15): Python/Streamlit implementation with full automation
- **v1.0**: Original manual process documentation

## License

Internal use only - Applied Materials SmartFactory Rx
