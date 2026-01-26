# SFRx Migration Validation Checklist

**Release:** ABL_Risa-R3-Upstream_DevtoQA  
**Date:** _________________  
**Executed By:** _________________  
**Migration Window:** From _________ To _________  

---

## Pre-Migration Validation

### Environment Verification
- [ ] Dev Server (WA02836D) is accessible and running
- [ ] QA Server (WA01929Q) is accessible and running
- [ ] Network connectivity verified (ping successful)
- [ ] SMB shares accessible on both servers
- [ ] User has Administrator privileges

### File & Path Verification
- [ ] E3 package file (.e3pkg) exists on Dev server
- [ ] Migration folder exists: `E:\Applied Materials\SmartFactoryRx_ABL\Migration`
- [ ] Equipment .json files present (count: _____)
- [ ] Equipment .csv files present (count: _____)
- [ ] Sufficient disk space on QA server (minimum 5 GB free)

### System Verification
- [ ] SFRx ABL QA instance is version 2.2.1 or above
- [ ] E3 (EES) system is accessible
- [ ] Both SFRx services are currently Running on QA
- [ ] Backup location identified for rollback

### Pre-Requisite Sign-off
- [ ] Strategies have been validated by SFRx Technical Support
- [ ] Migration approval received from release manager
- [ ] Stakeholders notified of migration window
- [ ] Backup of current QA environment completed

---

## Step 1: Pre-Flight Checks (Automated)

**Execution Time:** Start _________ End _________

### Script Output Review
```
Pre-Flight Checks:
☐ Admin Rights: ✓ PASS / ✗ FAIL
☐ Dev Server Connectivity: ✓ PASS / ✗ FAIL
☐ QA Server Connectivity: ✓ PASS / ✗ FAIL
☐ Dev Migration Path Exists: ✓ PASS / ✗ FAIL
```

### Action Items
- [ ] All checks passed (GREEN)
- [ ] If any failed, document issue and resolve:
  
  **Issue:** _________________________________________________
  
  **Resolution:** ____________________________________________
  
  **Retry Result:** ✓ PASS / ✗ FAIL

### Sign-off
- [ ] Pre-flight checks approved
- [ ] Proceed to Step 2

---

## Step 2: Copy E3 Package (Automated)

**Execution Time:** Start _________ End _________

### File Details
- [ ] Source Path: `\\WA02836D\E$\Applied Materials\SmartFactoryRx_ABL\Migration`
- [ ] Destination Path: `\\WA01929Q\E$\Applied Materials\SmartFactoryRx_ABL\Migration`
- [ ] E3 Package File: _________________________ (Size: _____ GB)

### Script Output
- [ ] Files listed for review
- [ ] User confirmed: yes / no
- [ ] Transfer started
- [ ] Transfer completed successfully
- [ ] File integrity verified (checksums match)

### Verification
```powershell
# Manual verification command
Get-ChildItem "\\WA01929Q\E$\Applied Materials\SmartFactoryRx_ABL\Migration\*.e3pkg"
```

- [ ] File visible on QA server
- [ ] File size matches source

### Sign-off
- [ ] E3 package copy completed
- [ ] Proceed to Step 3

---

## Step 3: Copy Equipment Files (Automated)

**Execution Time:** Start _________ End _________

### File Summary
- [ ] Total Equipment to Migrate: 23
- [ ] Expected Files:
  - [ ] JSON files (equipment configs): 23
  - [ ] CSV files (scripts/run boundaries): 23
  - [ ] Total files: 46

### Equipment List Status
| Equipment | JSON | CSV | Status |
|-----------|------|-----|--------|
| RT-0175-001 | ☐ | ☐ | ✓/✗ |
| RT-0177-001 | ☐ | ☐ | ✓/✗ |
| RT-0179-001 | ☐ | ☐ | ✓/✗ |
| RT-0181-001 | ☐ | ☐ | ✓/✗ |
| RT-0183-001 | ☐ | ☐ | ✓/✗ |
| RT-0185-001 | ☐ | ☐ | ✓/✗ |
| RT-0187-001 | ☐ | ☐ | ✓/✗ |
| RT-0189-001 | ☐ | ☐ | ✓/✗ |
| RT-0191-001 | ☐ | ☐ | ✓/✗ |
| RT-0193-001 | ☐ | ☐ | ✓/✗ |
| RT-0195-001 | ☐ | ☐ | ✓/✗ |
| RT-0197-001 | ☐ | ☐ | ✓/✗ |
| RT-0199-001 | ☐ | ☐ | ✓/✗ |
| RX-0201 | ☐ | ☐ | ✓/✗ |
| RX-0203 | ☐ | ☐ | ✓/✗ |
| RX-0205 | ☐ | ☐ | ✓/✗ |
| RX-0207 | ☐ | ☐ | ✓/✗ |
| RX-0217 | ☐ | ☐ | ✓/✗ |
| RX-0219 | ☐ | ☐ | ✓/✗ |
| RX-0221 | ☐ | ☐ | ✓/✗ |
| RX-0223 | ☐ | ☐ | ✓/✗ |

### Script Output
- [ ] Equipment files listed for review
- [ ] User confirmed: yes / no
- [ ] Transfer started
- [ ] Transfer completed successfully
- [ ] All 46 files copied (23 JSON + 23 CSV)

### Verification
```powershell
# Count files on QA server
(Get-ChildItem "\\WA01929Q\E$\...\Migration\*.json" | Measure-Object).Count
(Get-ChildItem "\\WA01929Q\E$\...\Migration\*.csv" | Measure-Object).Count
```

- [ ] JSON files: _____ (should be 23)
- [ ] CSV files: _____ (should be 23)
- [ ] Total: _____ (should be 46)

### Any Failed Files
```
Failed Equipment: ________________________
Reason: ____________________________________
Action Taken: ______________________________
Retry Status: ✓ Success / ✗ Still Failed
```

### Sign-off
- [ ] Equipment files copy completed
- [ ] Proceed to Step 4

---

## Step 4: Backup Existing Objects (Automated)

**Execution Time:** Start _________ End _________

### Backup Configuration
- [ ] Backup Suffix: `_BKP-20260126` (or current date)
- [ ] Backup Location: Same location with suffix
- [ ] Example: `Portal` → `Portal_BKP-20260126`

### Objects to Backup
```
Location: E:\Applied Materials\SmartFactoryRx_ABL\Portal
```

### Script Output
- [ ] Objects listed for review
- [ ] User confirmed: yes / no
- [ ] Backup renaming started
- [ ] Backup renaming completed successfully

### Verification - Before Backup
```powershell
Get-ChildItem "E:\Applied Materials\SmartFactoryRx_ABL\Portal" -Directory |
    Where-Object Name -notlike "*BKP*" | Select-Object Name
```

**Count of objects to backup:** _____

### Verification - After Backup
```powershell
Get-ChildItem "E:\Applied Materials\SmartFactoryRx_ABL\Portal" -Directory |
    Where-Object Name -like "*BKP*" | Select-Object Name
```

- [ ] All original objects backed up with suffix
- [ ] Backed up object count: _____ (should equal "before" count)

### Backup Documentation
- [ ] Backup date/time recorded: _________________
- [ ] Backup location verified
- [ ] Rollback procedure documented (see README)

### Sign-off
- [ ] Backup completed successfully
- [ ] Safety point established
- [ ] Proceed to Step 5

---

## Step 5: Restart SFRx Services (Automated)

**Execution Time:** Start _________ End _________

### Services to Restart
- [ ] SFRx_ABL_E3Client
- [ ] SFRx_ABL_Portal

### Pre-Restart Status
```powershell
Get-Service -ComputerName WA01929Q -Name "SFRx_ABL*"
```

| Service | Status | Start Time |
|---------|--------|-----------|
| SFRx_ABL_E3Client | _________ | _________ |
| SFRx_ABL_Portal | _________ | _________ |

### Script Output
- [ ] Services listed for restart
- [ ] User confirmed: yes / no
- [ ] E3Client restart initiated
  - Restart time: _________
  - Completion time: _________
- [ ] Portal restart initiated
  - Restart time: _________
  - Completion time: _________
- [ ] Both services restarted successfully

### Post-Restart Status
```powershell
Get-Service -ComputerName WA01929Q -Name "SFRx_ABL*"
```

| Service | Status | Start Time |
|---------|--------|-----------|
| SFRx_ABL_E3Client | ✓ Running | _________ |
| SFRx_ABL_Portal | ✓ Running | _________ |

### Service Health Verification
- [ ] E3Client service is Running (green)
- [ ] Portal service is Running (green)
- [ ] Wait 5 minutes for full initialization
- [ ] No error messages in Event Viewer (optional manual check)

### Sign-off
- [ ] Services restarted successfully
- [ ] Services running and healthy
- [ ] Migration script automation complete

---

## Post-Migration Verification (Manual Steps)

### SFRx Portal Access
- [ ] Connect to QA Portal: https://smart-factory-abl-q.k8s.abbvienet.com/
- [ ] Login successful: yes / no
- [ ] New equipment visible in system
- [ ] Configuration data loaded correctly

### E3 System Verification (Manual - Next Step)
- [ ] Open E3 (EES) Launcher on QA server
- [ ] Verify imported objects:
  - [ ] Expected objects present
  - [ ] Object properties correct
  - [ ] No duplicate or corrupt objects
- [ ] Run domain mapping verification (automated GUI test later)

### CLI Verification (Manual - Next Step)
```powershell
# On QA server in E:\Applied Materials\SmartFactoryRx_ABL\CLI\bin
sfrxcli -i --env ABL
ee -f "path\to\exported-file.json"  # Lists equipment
es -f "path\to\exported-file.csv"   # Lists scripts
```

- [ ] Equipment imports verified via CLI
- [ ] Scripts imports verified via CLI
- [ ] No error messages from CLI commands

### Production Readiness
- [ ] All 23 equipment successfully migrated
- [ ] No objects missing or corrupted
- [ ] Services stable (no restarts needed)
- [ ] Performance acceptable (no slowdowns)
- [ ] Users can access Portal normally

---

## Rollback Criteria

Check one if migration must be rolled back:

- [ ] E3 package import failed
- [ ] Critical equipment configuration missing
- [ ] Portal services repeatedly crashing
- [ ] Performance severely degraded
- [ ] User reports critical issues
- [ ] Stakeholder requests rollback

### Rollback Execution

If any rollback criteria met:

1. **Execute Rollback**
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

2. **Verify Rollback**
   - [ ] Original objects restored
   - [ ] Services running
   - [ ] Portal accessible
   - [ ] Users notified

3. **Document Issue**
   
   **Issue Description:** _________________________________
   
   **Root Cause:** ________________________________________
   
   **Remediation:** ________________________________________
   
   **Retry Date:** _________________________________________

- [ ] Rollback completed
- [ ] Issue documented for remediation

---

## Final Sign-Off

### Overall Migration Status

| Item | Status | Sign-off |
|------|--------|----------|
| Pre-Flight Checks | ✓ / ✗ | ___________ |
| E3 Package Copy | ✓ / ✗ | ___________ |
| Equipment Files Copy | ✓ / ✗ | ___________ |
| Object Backup | ✓ / ✗ | ___________ |
| Service Restart | ✓ / ✗ | ___________ |
| Portal Access | ✓ / ✗ | ___________ |
| E3 Verification | ✓ / ✗ | ___________ |
| CLI Verification | ✓ / ✗ | ___________ |

### Migration Result

☐ **SUCCESS** - All steps passed, new release in production

☐ **ROLLBACK** - Issues encountered, reverted to previous version

### Overall Sign-Off

**Migration Approved By:**

Name: _________________________  
Title: _________________________  
Date/Time: _________________________  
Signature: _________________________  

---

## Attachments

- [ ] Log file: `C:\Logs\SFRx-Migration\migration_*.log`
- [ ] Screenshots (as required):
  - [ ] Pre-flight checks passed
  - [ ] E3 import success
  - [ ] Portal access confirmation
  - [ ] Service status (all Running)
- [ ] Any error messages or issues documented

---

## Notes & Comments

```
_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________
```

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Prepared By:** Automation Team
