#=============================================================================
# SFRx ABL Migration Automation - Phase 1 (Human-in-the-Loop)
# Purpose: Automate file transfers, folder operations, and service restarts
# Date: January 2026
# Author: Automation Team
#=============================================================================

param(
    [string]$LogPath = "C:\Logs\SFRx-Migration",
    [string]$ConfigFile = "$PSScriptRoot\migration-config.ps1"
)

#region Configuration
# Load configuration from external file if it exists
if (Test-Path $ConfigFile) {
    . $ConfigFile
} else {
    # Default configuration
    $Config = @{
        DevServer = "WA02836D"
        DevServerIP = "192.168.x.x"  # Update with actual IP
        QAServer = "WA01929Q"
        QAServerIP = "192.168.x.x"   # Update with actual IP
        DevMigrationPath = "E:\Applied Materials\SmartFactoryRx_ABL\Migration"
        QAMigrationPath = "E:\Applied Materials\SmartFactoryRx_ABL\Migration"
        BackupSuffix = "_BKP-$(Get-Date -Format 'yyyyMMdd')"
        ReleaseDate = Get-Date -Format 'yyyyMMdd'
        LogLevel = "INFO"  # INFO, WARNING, ERROR
        Equipment = @(
            "RT-0175-001", "RT-0177-001", "RT-0179-001", "RT-0181-001", "RT-0183-001",
            "RT-0185-001", "RT-0187-001", "RT-0189-001", "RT-0191-001", "RT-0193-001",
            "RT-0195-001", "RT-0197-001", "RT-0199-001", "RX-0201", "RX-0203",
            "RX-0205", "RX-0207", "RX-0217", "RX-0219", "RX-0221", "RX-0223"
        )
    }
}
#endregion

#region Logging Setup
if (-not (Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
}

$LogFile = Join-Path $LogPath "migration_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARNING", "ERROR", "SUCCESS")]
        [string]$Level = "INFO",
        [switch]$NoNewLine
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Console output with colors
    switch ($Level) {
        "ERROR"   { Write-Host $logEntry -ForegroundColor Red }
        "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        "INFO"    { Write-Host $logEntry -ForegroundColor Cyan }
    }
    
    # File output
    Add-Content -Path $LogFile -Value $logEntry
}

Write-Log "===== SFRx Migration Automation Started =====" -Level "INFO"
Write-Log "Log file: $LogFile" -Level "INFO"
#endregion

#region Helper Functions
function Confirm-Action {
    param(
        [string]$Title,
        [string]$Description,
        [string]$Action
    )
    
    Write-Host "`n" -ForegroundColor Cyan
    Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║ $Title" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host $Description -ForegroundColor White
    Write-Host $Action -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "Do you want to proceed? (yes/no)"
    return ($response -eq "yes")
}

function Test-ServerConnectivity {
    param([string]$ServerIP)
    
    Write-Log "Testing connectivity to $ServerIP..." -Level "INFO"
    
    if (Test-Connection -ComputerName $ServerIP -Count 1 -Quiet) {
        Write-Log "✓ Server $ServerIP is reachable" -Level "SUCCESS"
        return $true
    } else {
        Write-Log "✗ Server $ServerIP is NOT reachable" -Level "ERROR"
        return $false
    }
}

function Get-AdminRights {
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
    return $isAdmin
}
#endregion

#region Pre-Flight Checks
function Invoke-PreFlightChecks {
    Write-Log "Starting pre-flight checks..." -Level "INFO"
    
    $checks = @{
        "Admin Rights" = $false
        "Dev Server Connectivity" = $false
        "QA Server Connectivity" = $false
        "Dev Migration Path Exists" = $false
    }
    
    # Check 1: Admin Rights
    if (Get-AdminRights) {
        Write-Log "✓ Running with administrator privileges" -Level "SUCCESS"
        $checks["Admin Rights"] = $true
    } else {
        Write-Log "✗ NOT running as administrator" -Level "WARNING"
    }
    
    # Check 2: Dev Server Connectivity
    if (Test-ServerConnectivity $Config.DevServerIP) {
        $checks["Dev Server Connectivity"] = $true
    }
    
    # Check 3: QA Server Connectivity
    if (Test-ServerConnectivity $Config.QAServerIP) {
        $checks["QA Server Connectivity"] = $true
    }
    
    # Check 4: Dev Migration Path
    if (Test-Path "\\$($Config.DevServer)\E$\Applied Materials\SmartFactoryRx_ABL\Migration") {
        Write-Log "✓ Dev migration path accessible" -Level "SUCCESS"
        $checks["Dev Migration Path Exists"] = $true
    } else {
        Write-Log "✗ Dev migration path NOT accessible" -Level "WARNING"
    }
    
    # Summary
    Write-Host "`n════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "PRE-FLIGHT CHECKS SUMMARY" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
    $checks.GetEnumerator() | ForEach-Object {
        $status = if ($_.Value) { "✓ PASS" } else { "✗ FAIL" }
        $color = if ($_.Value) { "Green" } else { "Red" }
        Write-Host "$($_.Name): $status" -ForegroundColor $color
    }
    Write-Host "════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
    
    return $checks.Values -contains $false ? $false : $true
}
#endregion

#region File Transfer Functions
function Copy-FilesSMB {
    param(
        [string]$SourceServer,
        [string]$DestinationServer,
        [string]$SourcePath,
        [string]$DestinationPath,
        [string]$FilePattern = "*"
    )
    
    $sourceSMB = "\\$SourceServer\$(($SourcePath -replace '^([a-zA-Z]):', '$1$') -replace '\\', '\' )"
    $destSMB = "\\$DestinationServer\$(($DestinationPath -replace '^([a-zA-Z]):', '$1$') -replace '\\', '\' )"
    
    Write-Log "Preparing to copy files:" -Level "INFO"
    Write-Log "  FROM: $sourceSMB\$FilePattern" -Level "INFO"
    Write-Log "  TO:   $destSMB" -Level "INFO"
    
    try {
        # Count files first
        $files = Get-ChildItem -Path "$sourceSMB\$FilePattern" -ErrorAction Stop
        Write-Log "Found $($files.Count) file(s) to copy" -Level "INFO"
        
        # Show file details
        Write-Host "`nFiles to be copied:" -ForegroundColor Yellow
        $files | ForEach-Object {
            $sizeGB = [math]::Round($_.Length / 1GB, 2)
            Write-Host "  - $($_.Name) ($sizeGB GB)"
        }
        
        if (-not (Confirm-Action "File Transfer Confirmation" `
            "Review the files above that will be copied." `
            "This may take several minutes depending on file size.")) {
            Write-Log "File transfer cancelled by user" -Level "WARNING"
            return $false
        }
        
        # Ensure destination exists
        if (-not (Test-Path $destSMB)) {
            New-Item -ItemType Directory -Path $destSMB -Force | Out-Null
        }
        
        # Copy files with progress
        $counter = 0
        $files | ForEach-Object {
            $counter++
            Write-Host "Copying [$counter/$($files.Count)] $($_.Name)..." -ForegroundColor Cyan
            Copy-Item -Path $_.FullName -Destination $destSMB -Force -ErrorAction Stop
            Write-Log "✓ Copied: $($_.Name)" -Level "SUCCESS"
        }
        
        Write-Log "✓ File transfer completed successfully" -Level "SUCCESS"
        return $true
    }
    catch {
        Write-Log "✗ File transfer failed: $_" -Level "ERROR"
        return $false
    }
}

function Copy-EquipmentFiles {
    param(
        [string]$SourceServer,
        [string]$DestinationServer,
        [string]$MigrationPath,
        [string[]]$EquipmentList
    )
    
    $sourcePath = "\\$SourceServer\E$\Applied Materials\SmartFactoryRx_ABL\Migration"
    $destPath = "\\$DestinationServer\E$\Applied Materials\SmartFactoryRx_ABL\Migration"
    
    Write-Log "Preparing to copy equipment files ($($EquipmentList.Count) equipment)" -Level "INFO"
    
    try {
        # List files that will be copied
        $fileCount = 0
        Write-Host "`nEquipment files to be copied:" -ForegroundColor Yellow
        
        foreach ($equipment in $EquipmentList) {
            $jsonFile = "$sourcePath\*-$equipment.json"
            $csvFile = "$sourcePath\*-$equipment.csv"
            
            $jsonFiles = Get-ChildItem -Path $jsonFile -ErrorAction SilentlyContinue
            $csvFiles = Get-ChildItem -Path $csvFile -ErrorAction SilentlyContinue
            
            if ($jsonFiles) { $fileCount++; Write-Host "  - JSON: $($jsonFiles[0].Name)" }
            if ($csvFiles) { $fileCount++; Write-Host "  - CSV:  $($csvFiles[0].Name)" }
        }
        
        Write-Log "Found $fileCount file(s) for equipment" -Level "INFO"
        
        if (-not (Confirm-Action "Equipment File Transfer" `
            "About to copy $fileCount equipment configuration files." `
            "Source: $sourcePath`nDestination: $destPath")) {
            Write-Log "Equipment file transfer cancelled by user" -Level "WARNING"
            return $false
        }
        
        # Copy equipment files
        $counter = 0
        foreach ($equipment in $EquipmentList) {
            $counter++
            Write-Host "Copying equipment [$counter/$($EquipmentList.Count)] $equipment..." -ForegroundColor Cyan
            
            # Copy JSON files
            Get-ChildItem -Path "$sourcePath\*-$equipment.json" -ErrorAction SilentlyContinue | 
                ForEach-Object { Copy-Item -Path $_.FullName -Destination $destPath -Force }
            
            # Copy CSV files
            Get-ChildItem -Path "$sourcePath\*-$equipment.csv" -ErrorAction SilentlyContinue | 
                ForEach-Object { Copy-Item -Path $_.FullName -Destination $destPath -Force }
            
            Write-Log "✓ Copied equipment files for: $equipment" -Level "SUCCESS"
        }
        
        Write-Log "✓ All equipment files transferred successfully" -Level "SUCCESS"
        return $true
    }
    catch {
        Write-Log "✗ Equipment file transfer failed: $_" -Level "ERROR"
        return $false
    }
}
#endregion

#region Backup Functions
function Backup-SFRxObjects {
    param([string]$Server)
    
    $basePath = "\\$Server\E$\Applied Materials\SmartFactoryRx_$($Config.DevServer.Substring(0,3))\Portal"
    
    Write-Log "Preparing to backup SFRx objects on $Server" -Level "INFO"
    
    try {
        $objectsPath = "$basePath"
        
        if (-not (Test-Path $objectsPath)) {
            Write-Log "✗ Objects path not found: $objectsPath" -Level "ERROR"
            return $false
        }
        
        # Get list of objects to backup
        $objects = Get-ChildItem -Path $objectsPath -Directory | Where-Object { $_.Name -notlike "*BKP*" }
        
        Write-Host "`nObjects to be backed up:" -ForegroundColor Yellow
        $objects | ForEach-Object { Write-Host "  - $($_.Name)" }
        
        if (-not (Confirm-Action "Backup SFRx Objects" `
            "About to backup $($objects.Count) SFRx objects with suffix: $($Config.BackupSuffix)" `
            "Backed up objects will be preserved for rollback.")) {
            Write-Log "Backup cancelled by user" -Level "WARNING"
            return $false
        }
        
        # Rename objects with backup suffix
        $counter = 0
        $objects | ForEach-Object {
            $counter++
            $newName = "$($_.Name)$($Config.BackupSuffix)"
            Write-Host "Backing up [$counter/$($objects.Count)] $($_.Name) → $newName..." -ForegroundColor Cyan
            Rename-Item -Path $_.FullName -NewName $newName -Force
            Write-Log "✓ Backed up: $($_.Name) → $newName" -Level "SUCCESS"
        }
        
        Write-Log "✓ Backup completed successfully" -Level "SUCCESS"
        return $true
    }
    catch {
        Write-Log "✗ Backup failed: $_" -Level "ERROR"
        return $false
    }
}
#endregion

#region Service Management Functions
function Restart-SFRxServices {
    param([string]$Server)
    
    $services = @(
        "SFRx_ABL_E3Client",
        "SFRx_ABL_Portal"
    )
    
    Write-Log "Preparing to restart services on $Server" -Level "INFO"
    
    try {
        Write-Host "`nServices to be restarted:" -ForegroundColor Yellow
        $services | ForEach-Object { Write-Host "  - $_" }
        
        if (-not (Confirm-Action "Service Restart Confirmation" `
            "About to restart $($services.Count) SFRx services on $Server." `
            "This may cause a brief service interruption.")) {
            Write-Log "Service restart cancelled by user" -Level "WARNING"
            return $false
        }
        
        $counter = 0
        foreach ($service in $services) {
            $counter++
            Write-Host "Restarting [$counter/$($services.Count)] $service..." -ForegroundColor Cyan
            
            # Try local if on same machine, otherwise use WinRM
            if ($env:COMPUTERNAME -eq $Server) {
                Restart-Service -Name $service -Force -ErrorAction Stop
            } else {
                Invoke-Command -ComputerName $Server -ScriptBlock {
                    param($svc)
                    Restart-Service -Name $svc -Force
                } -ArgumentList $service -ErrorAction Stop
            }
            
            Write-Log "✓ Restarted service: $service" -Level "SUCCESS"
            Start-Sleep -Seconds 5
        }
        
        Write-Log "✓ All services restarted successfully" -Level "SUCCESS"
        return $true
    }
    catch {
        Write-Log "✗ Service restart failed: $_" -Level "ERROR"
        return $false
    }
}

function Get-ServiceStatus {
    param([string]$Server)
    
    Write-Log "Getting service status on $Server..." -Level "INFO"
    
    try {
        $services = @("SFRx_ABL_E3Client", "SFRx_ABL_Portal")
        
        Write-Host "`n════════════════════════════════════════════════════════" -ForegroundColor Cyan
        Write-Host "SERVICE STATUS ON $Server" -ForegroundColor Cyan
        Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
        
        foreach ($service in $services) {
            if ($env:COMPUTERNAME -eq $Server) {
                $svcStatus = Get-Service -Name $service -ErrorAction SilentlyContinue
            } else {
                $svcStatus = Invoke-Command -ComputerName $Server -ScriptBlock {
                    param($svc)
                    Get-Service -Name $svc -ErrorAction SilentlyContinue
                } -ArgumentList $service
            }
            
            if ($svcStatus) {
                $status = $svcStatus.Status
                $color = if ($status -eq "Running") { "Green" } else { "Red" }
                Write-Host "$service : $status" -ForegroundColor $color
                Write-Log "Service $service is $status on $Server" -Level "INFO"
            }
        }
        
        Write-Host "════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
    }
    catch {
        Write-Log "✗ Failed to get service status: $_" -Level "ERROR"
    }
}
#endregion

#region Main Menu
function Show-MainMenu {
    Clear-Host
    Write-Host "`n" -ForegroundColor Cyan
    Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   SFRx ABL Migration Automation - Phase 1              ║" -ForegroundColor Cyan
    Write-Host "║   Human-in-the-Loop Mode                              ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    
    Write-Host "`nCONFIGURATION SUMMARY:" -ForegroundColor Yellow
    Write-Host "  Dev Server:  $($Config.DevServer) ($($Config.DevServerIP))" -ForegroundColor Cyan
    Write-Host "  QA Server:   $($Config.QAServer) ($($Config.QAServerIP))" -ForegroundColor Cyan
    Write-Host "  Release:     ABL_Risa-R3-Upstream_DevtoQA_$($Config.ReleaseDate)" -ForegroundColor Cyan
    Write-Host "  Log File:    $LogFile" -ForegroundColor Cyan
    
    Write-Host "`nMAIN MENU:" -ForegroundColor Yellow
    Write-Host "  [1] Pre-Flight Checks" -ForegroundColor Cyan
    Write-Host "  [2] Copy E3 Package & Export Files (DEV → QA)" -ForegroundColor Cyan
    Write-Host "  [3] Copy Equipment Files (DEV → QA)" -ForegroundColor Cyan
    Write-Host "  [4] Backup Existing SFRx Objects (QA)" -ForegroundColor Cyan
    Write-Host "  [5] Restart SFRx Services (QA)" -ForegroundColor Cyan
    Write-Host "  [6] Check Service Status (QA)" -ForegroundColor Cyan
    Write-Host "  [7] Full Automation (Steps 1-5)" -ForegroundColor Cyan
    Write-Host "  [8] View Migration Log" -ForegroundColor Cyan
    Write-Host "  [Q] Exit" -ForegroundColor Cyan
    Write-Host ""
}

function Invoke-MainMenu {
    do {
        Show-MainMenu
        $choice = Read-Host "Select an option"
        
        switch ($choice) {
            "1" {
                if (Invoke-PreFlightChecks) {
                    Write-Host "`nPre-flight checks PASSED - Ready to proceed with migration" -ForegroundColor Green
                } else {
                    Write-Host "`nPre-flight checks FAILED - Please resolve issues before proceeding" -ForegroundColor Red
                }
                Read-Host "`nPress Enter to continue"
            }
            
            "2" {
                Copy-FilesSMB -SourceServer $Config.DevServer `
                    -DestinationServer $Config.QAServer `
                    -SourcePath "E:\Applied Materials\SmartFactoryRx_ABL\Migration" `
                    -DestinationPath "E:\Applied Materials\SmartFactoryRx_ABL\Migration" `
                    -FilePattern "*.e3pkg"
                Read-Host "`nPress Enter to continue"
            }
            
            "3" {
                Copy-EquipmentFiles -SourceServer $Config.DevServer `
                    -DestinationServer $Config.QAServer `
                    -MigrationPath "E:\Applied Materials\SmartFactoryRx_ABL\Migration" `
                    -EquipmentList $Config.Equipment
                Read-Host "`nPress Enter to continue"
            }
            
            "4" {
                Backup-SFRxObjects -Server $Config.QAServer
                Read-Host "`nPress Enter to continue"
            }
            
            "5" {
                Restart-SFRxServices -Server $Config.QAServer
                Read-Host "`nPress Enter to continue"
            }
            
            "6" {
                Get-ServiceStatus -Server $Config.QAServer
                Read-Host "`nPress Enter to continue"
            }
            
            "7" {
                Write-Host "`nRunning FULL AUTOMATION sequence...`n" -ForegroundColor Yellow
                
                if (Invoke-PreFlightChecks) {
                    Copy-FilesSMB -SourceServer $Config.DevServer -DestinationServer $Config.QAServer `
                        -SourcePath "E:\Applied Materials\SmartFactoryRx_ABL\Migration" `
                        -DestinationPath "E:\Applied Materials\SmartFactoryRx_ABL\Migration" -FilePattern "*.e3pkg"
                    
                    Copy-EquipmentFiles -SourceServer $Config.DevServer -DestinationServer $Config.QAServer `
                        -MigrationPath "E:\Applied Materials\SmartFactoryRx_ABL\Migration" `
                        -EquipmentList $Config.Equipment
                    
                    Backup-SFRxObjects -Server $Config.QAServer
                    Restart-SFRxServices -Server $Config.QAServer
                    
                    Write-Log "✓ FULL AUTOMATION COMPLETED SUCCESSFULLY" -Level "SUCCESS"
                } else {
                    Write-Log "✗ Pre-flight checks failed - Full automation aborted" -Level "ERROR"
                }
                
                Read-Host "`nPress Enter to continue"
            }
            
            "8" {
                if (Test-Path $LogFile) {
                    notepad $LogFile
                } else {
                    Write-Host "No log file found yet" -ForegroundColor Red
                }
            }
            
            "Q" {
                Write-Log "Migration automation script closed by user" -Level "INFO"
                Write-Host "`nThank you for using SFRx Migration Automation!`n" -ForegroundColor Green
                exit
            }
            
            default {
                Write-Host "Invalid option. Please try again." -ForegroundColor Red
                Start-Sleep -Seconds 2
            }
        }
    } while ($true)
}
#endregion

#region Main Execution
if (-not (Get-AdminRights)) {
    Write-Host "`nWARNING: This script requires Administrator privileges!`n" -ForegroundColor Red
    $response = Read-Host "Do you want to re-run as Administrator? (yes/no)"
    if ($response -eq "yes") {
        Start-Process powershell -ArgumentList "-File `"$PSCommandPath`"" -Verb RunAs
    }
    exit
}

Invoke-MainMenu
#endregion
