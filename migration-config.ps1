#=============================================================================
# SFRx Migration Configuration File
# Update these values before running the migration script
#=============================================================================

$Config = @{
    # Server Information
    DevServer = "WA02836D"
    DevServerIP = "192.168.x.x"        # UPDATE: IP address of Dev server
    QAServer = "WA01929Q"
    QAServerIP = "192.168.x.x"         # UPDATE: IP address of QA server
    
    # Paths
    DevMigrationPath = "E:\Applied Materials\SmartFactoryRx_ABL\Migration"
    QAMigrationPath = "E:\Applied Materials\SmartFactoryRx_ABL\Migration"
    
    # Backup Configuration
    BackupSuffix = "_BKP-$(Get-Date -Format 'yyyyMMdd')"
    ReleaseDate = Get-Date -Format 'yyyyMMdd'
    
    # Release Information
    ReleaseName = "ABL_Risa-R3-Upstream_DevtoQA"
    
    # Logging
    LogLevel = "INFO"  # INFO, WARNING, ERROR
    
    # Equipment List (All 23 equipment)
    Equipment = @(
        "RT-0175-001", "RT-0177-001", "RT-0179-001", "RT-0181-001", "RT-0183-001",
        "RT-0185-001", "RT-0187-001", "RT-0189-001", "RT-0191-001", "RT-0193-001",
        "RT-0195-001", "RT-0197-001", "RT-0199-001", "RX-0201", "RX-0203",
        "RX-0205", "RX-0207", "RX-0217", "RX-0219", "RX-0221", "RX-0223"
    )
    
    # Services to Restart
    Services = @(
        "SFRx_ABL_E3Client",
        "SFRx_ABL_Portal"
    )
}

# Export configuration for use in main script
Export-ModuleMember -Variable Config
