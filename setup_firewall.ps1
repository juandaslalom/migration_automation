# ============================================================
# Firewall rules to restrict Streamlit app access by IP
# Run this script as Administrator
# ============================================================

# --- Configuration ---
$AppPort     = 8501                          # Streamlit port
$RuleName    = "SFRx Migration App"


# --- Remove old rules if they exist ---
Remove-NetFirewallRule -DisplayName "$RuleName - Allow" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "$RuleName - Block" -ErrorAction SilentlyContinue

# --- Block everyone on that port ---
New-NetFirewallRule `
    -DisplayName "$RuleName - Block" `
    -Direction Inbound `
    -Action Block `
    -Protocol TCP `
    -LocalPort $AppPort `
    -Profile Any

# --- Allow only the listed IPs ---
New-NetFirewallRule `
    -DisplayName "$RuleName - Allow" `
    -Direction Inbound `
    -Action Allow `
    -Protocol TCP `
    -LocalPort $AppPort `
    -RemoteAddress $AllowedIPs `
    -Profile Any

Write-Host ""
Write-Host "Firewall configured:" -ForegroundColor Green
Write-Host "  Port      : $AppPort"
Write-Host "  Allowed   : $($AllowedIPs -join ', ')"
Write-Host "  All other IPs are BLOCKED on port $AppPort"
Write-Host ""
Write-Host "To verify:  Get-NetFirewallRule -DisplayName 'SFRx Migration App*' | Format-Table"
Write-Host "To remove:  Remove-NetFirewallRule -DisplayName 'SFRx Migration App - Allow'"
Write-Host "            Remove-NetFirewallRule -DisplayName 'SFRx Migration App - Block'"
