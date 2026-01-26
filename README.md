# SFRx Migration Automation - Phase 1 Quick Start Guide

## Overview
This is a **human-in-the-loop** PowerShell automation for the SFRx ABL migration. You maintain full control—the script automates repetitive tasks but requires your approval at each step.

---

## Prerequisites

### System Requirements
- Windows Server 2016 or newer
- PowerShell 5.0 or newer
- **Administrator privileges** (script will prompt for elevation if needed)
- Network access to both Dev and QA servers
- Remote Desktop Protocol (RDP) or direct server access
- WinRM enabled for remote service management (optional)

### Verify Prerequisites
```powershell
# Check PowerShell version
$PSVersionTable.PSVersion

# Check if running as admin
[Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
```

---

## Installation & Setup

### Step 1: Configure Settings
Edit `migration-config.ps1` and update these values:

```powershell
DevServerIP = "10.x.x.x"          # UPDATE: Your Dev server IP
QAServerIP = "10.x.x.x"           # UPDATE: Your QA server IP
```

### Step 2: Create Log Directory
```powershell
# On your local machine
New-Item -ItemType Directory -Path "C:\Logs\SFRx-Migration" -Force
```

### Step 3: Run the Script
```powershell
# From PowerShell (run as Administrator)
cd "C:\Path\To\automation_abbvie"
.\SFRx-Migration-Automation.ps1

# OR with custom log path
.\SFRx-Migration-Automation.ps1 -LogPath "C:\Custom\Log\Path"
```

---

## How to Use

### Menu-Driven Operation
When you run the script, you'll see a menu:

```
[1] Pre-Flight Checks                    ← START HERE!
[2] Copy E3 Package & Export Files       ← Auto-copy from Dev to QA
[3] Copy Equipment Files                 ← Auto-copy 23 equipment configs
[4] Backup Existing SFRx Objects         ← Safety: adds _BKP suffix
[5] Restart SFRx Services                ← Auto-restart services
[6] Check Service Status                 ← Verify services are running
[7] Full Automation (Steps 1-5)          ← Run entire sequence
[8] View Migration Log                   ← See what happened
```

### Typical Workflow

#### Option A: Step-by-Step (Recommended for First Run)
```
1. Run Step [1] - Pre-Flight Checks
   ✓ Verify all systems are accessible
   ✓ Confirms connectivity and paths exist
   
2. Run Step [2] - Copy E3 Package
   ✓ You'll see list of files
   ✓ Type "yes" to proceed
   ✓ Progress shown in real-time
   
3. Run Step [3] - Copy Equipment Files
   ✓ Lists all 23 equipment
   ✓ Type "yes" to proceed
   ✓ Copies .json and .csv files
   
4. Run Step [4] - Backup Objects
   ✓ Shows objects to backup
   ✓ Type "yes" to rename with _BKP-20260126 suffix
   ✓ Preserves originals for rollback
   
5. Run Step [5] - Restart Services
   ✓ Shows services to restart
   ✓ Type "yes" to restart
   ✓ Waits 5 seconds between restarts
   
6. Run Step [6] - Check Service Status
   ✓ Verifies both services are Running
   ✓ Should show green status
```

#### Option B: Full Automation (For Experienced Users)
```
1. Verify pre-flight checks pass
2. Select Option [7] - Full Automation
3. Approve each step as prompted
4. Script handles all 5 steps automatically
```

---

## What Each Step Does

### [1] Pre-Flight Checks
Validates:
- ✓ Running as Administrator
- ✓ Dev server is reachable (ping)
- ✓ QA server is reachable (ping)
- ✓ Migration folder paths exist
- ✓ Network shares accessible

**Output:** Green checkmarks mean go ahead. Red X means fix that issue first.

### [2] Copy E3 Package Files
Automates:
- Finds all `.e3pkg` files on Dev server
- Shows file list with sizes
- Copies to QA server's same path
- Validates transfer completed

**Human Control:** You see files before copying, must type "yes"

### [3] Copy Equipment Files
Automates:
- Copies `.json` config files for all 23 equipment
- Copies `.csv` script/run boundary files
- Creates list: Equipment → Files being copied
- Parallel processing for speed

**Time:** ~5-10 minutes depending on network

### [4] Backup Existing Objects
Automates:
- Renames existing SFRx objects with `_BKP-20260126` suffix
- Creates rollback point safely
- Preserves all original configurations
- Lists all objects being backed up

**Example:** `Portal` → `Portal_BKP-20260126`

### [5] Restart Services
Automates:
- Restarts `SFRx_ABL_E3Client`
- Restarts `SFRx_ABL_Portal`
- Waits 5 seconds between restarts
- Services fully reload

**Duration:** ~30-60 seconds total

### [6] Check Service Status
Shows current status:
- Green = Running ✓
- Red = Stopped ✗
- Use anytime to verify services are healthy

---

## Understanding the Confirmations

After each step, you'll see:

```
╔════════════════════════════════════════════════════════╗
║ Copy E3 Package & Export Files (DEV → QA)             ║
╚════════════════════════════════════════════════════════╝
Review the files that will be copied.
This may take several minutes depending on file size.
Copying [\path\to\file.e3pkg] (2.5 GB)

Do you want to proceed? (yes/no)
```

**Type exactly:** `yes` or `no` (case-sensitive in display, but script accepts both)

---

## Logs & Documentation

### Log File Location
```
C:\Logs\SFRx-Migration\migration_20260126_143022.log
```

### Typical Log Output
```
[2026-01-26 14:30:22] [INFO] ===== SFRx Migration Automation Started =====
[2026-01-26 14:30:22] [INFO] Log file: C:\Logs\SFRx-Migration\migration_20260126_143022.log
[2026-01-26 14:30:23] [INFO] Testing connectivity to 192.168.1.10...
[2026-01-26 14:30:23] [SUCCESS] ✓ Server 192.168.1.10 is reachable
[2026-01-26 14:30:24] [INFO] Preparing to copy files:
[2026-01-26 14:30:24] [INFO]   FROM: \\WA02836D\E$\Applied Materials\SmartFactoryRx_ABL\Migration\*
[2026-01-26 14:30:24] [INFO]   TO:   \\WA01929Q\E$\Applied Materials\SmartFactoryRx_ABL\Migration
```

### View Log File
```powershell
# Option 1: From menu, select [8]
# Option 2: Open directly
notepad "C:\Logs\SFRx-Migration\migration_20260126_143022.log"
# Option 3: PowerShell
Get-Content "C:\Logs\SFRx-Migration\migration_20260126_143022.log" -Tail 50
```

---

## Troubleshooting

### Issue: "✗ Server X is NOT reachable"

**Cause:** Network connectivity problem

**Solutions:**
1. Check IP addresses in `migration-config.ps1`
2. Verify VPN connection if remote
3. Test ping manually:
   ```powershell
   ping 192.168.x.x
   ```
4. Check firewall rules

### Issue: "✗ Dev migration path NOT accessible"

**Cause:** SMB share not accessible

**Solutions:**
1. Verify paths exist on servers
2. Check you have read permissions
3. Test manually:
   ```powershell
   Test-Path "\\WA02836D\E$\Applied Materials\SmartFactoryRx_ABL\Migration"
   ```
4. Ensure Dev server share is accessible

### Issue: Service restart fails

**Cause:** WinRM not configured or services named differently

**Solutions:**
1. Verify service names on QA server:
   ```powershell
   Get-Service -ComputerName WA01929Q | Where-Object Name -like "SFRx*"
   ```
2. Update service names in `migration-config.ps1`
3. Ensure WinRM is enabled:
   ```powershell
   Enable-PSRemoting -Force
   ```

### Issue: "Permission denied" errors

**Cause:** Not running as Administrator

**Solutions:**
1. Script will auto-prompt for elevation
2. Or start PowerShell with "Run as Administrator"
3. Right-click PowerShell → "Run as Administrator"

---

## Manual Commands (If You Need to Run Manually)

### Copy Files via PowerShell
```powershell
# Copy E3 package
Copy-Item -Path "\\WA02836D\E$\Applied Materials\SmartFactoryRx_ABL\Migration\*.e3pkg" `
          -Destination "\\WA01929Q\E$\Applied Materials\SmartFactoryRx_ABL\Migration" -Force

# Copy single equipment config
Copy-Item -Path "\\WA02836D\E$\...\*-RT-0175-001.json" `
          -Destination "\\WA01929Q\E$\...\*" -Force
```

### Rename Objects for Backup
```powershell
# On QA server
Get-ChildItem -Path "E:\Applied Materials\SmartFactoryRx_ABL\Portal" -Directory |
    ForEach-Object { Rename-Item -Path $_.FullName -NewName "$($_.Name)_BKP-20260126" }
```

### Restart Services
```powershell
# Local restart
Restart-Service -Name "SFRx_ABL_E3Client" -Force
Restart-Service -Name "SFRx_ABL_Portal" -Force

# Remote restart via WinRM
Invoke-Command -ComputerName WA01929Q -ScriptBlock {
    Restart-Service -Name "SFRx_ABL_E3Client" -Force
    Restart-Service -Name "SFRx_ABL_Portal" -Force
}
```

### Check Service Status
```powershell
# Local
Get-Service -Name "SFRx_ABL*"

# Remote
Get-Service -ComputerName WA01929Q -Name "SFRx_ABL*"
```

---

## Rollback Procedure (If Migration Fails)

### Quick Rollback
```powershell
# Rename backed-up objects back to original names
Get-ChildItem -Path "E:\Applied Materials\SmartFactoryRx_ABL\Portal" -Directory |
    Where-Object Name -like "*_BKP*" |
    ForEach-Object { 
        $newName = $_.Name -replace "_BKP-\d+$", ""
        Rename-Item -Path $_.FullName -NewName $newName
    }

# Restart services
Restart-Service -Name "SFRx_ABL_E3Client" -Force
Restart-Service -Name "SFRx_ABL_Portal" -Force
```

---

## Migration Success Checklist

- [ ] Pre-flight checks all pass (green)
- [ ] E3 package copied (file size shown)
- [ ] 23 equipment files copied (46 files total: .json + .csv)
- [ ] Existing objects backed up (all have _BKP suffix)
- [ ] Services restarted
- [ ] Service status shows both Running (green)
- [ ] Log file created with no ERROR entries
- [ ] Verify new objects appear in E3 GUI (manual verification)

---

## Support & Next Steps

### What's NOT Automated Yet (Future Phases)

Phase 2 could add:
- E3 GUI validation (automated screenshots)
- CLI command execution (sfrxcli imports)
- PDF report generation
- Email notifications
- Automated testing/verification

### Contact
For issues or improvements, see migration log for details or contact the automation team.

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start Script | `.\SFRx-Migration-Automation.ps1` |
| View Log | Menu Option [8] or `notepad "C:\Logs\SFRx-Migration\*.log"` |
| Check Services | Menu Option [6] |
| Manual Service Restart | `Restart-Service -Name "SFRx_ABL_*" -Force` |
| Rollback | Run Quick Rollback commands above |

