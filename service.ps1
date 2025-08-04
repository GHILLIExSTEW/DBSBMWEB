# Background Service Manager for DBSBM Web Application
# PowerShell script to manage web services

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "help")]
    [string]$Command = "help"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

function Show-Help {
    Write-Host ""
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host "   DBSBM Background Service Manager" -ForegroundColor Yellow
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\service.ps1 [command]" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Green
    Write-Host "  start   - Start all web services in background" -ForegroundColor Gray
    Write-Host "  stop    - Stop all web services" -ForegroundColor Gray
    Write-Host "  restart - Restart all web services" -ForegroundColor Gray
    Write-Host "  status  - Show current service status" -ForegroundColor Gray
    Write-Host "  logs    - Show recent service logs" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\service.ps1 start" -ForegroundColor Gray
    Write-Host "  .\service.ps1 status" -ForegroundColor Gray
    Write-Host ""
}

function Start-Services {
    Write-Host "🚀 Starting DBSBM web services..." -ForegroundColor Green
    $process = Start-Process -FilePath "python" -ArgumentList "background_service_manager.py", "start" -NoNewWindow -PassThru
    Write-Host "✅ Service manager started with PID: $($process.Id)" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Your web application will be available at:" -ForegroundColor Cyan
    Write-Host "   - Flask App: http://localhost:5000" -ForegroundColor White
    Write-Host "   - Web Proxy: http://localhost" -ForegroundColor White
    Write-Host ""
    Write-Host "Use '.\service.ps1 status' to check service status" -ForegroundColor Yellow
}

function Stop-Services {
    Write-Host "🛑 Stopping DBSBM web services..." -ForegroundColor Red
    python background_service_manager.py stop
    Write-Host "✅ Services stopped" -ForegroundColor Green
}

function Restart-Services {
    Write-Host "🔄 Restarting DBSBM web services..." -ForegroundColor Yellow
    python background_service_manager.py restart
    Write-Host "✅ Services restarted" -ForegroundColor Green
}

function Show-Status {
    python background_service_manager.py status
}

function Show-Logs {
    Write-Host ""
    Write-Host "📋 Recent service logs:" -ForegroundColor Cyan
    Write-Host "==================" -ForegroundColor Cyan
    
    $logFiles = Get-ChildItem -Path "service_logs" -Filter "service_manager_*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    
    if ($logFiles) {
        $latestLog = $logFiles[0]
        Write-Host ""
        Write-Host "Latest log file: $($latestLog.Name)" -ForegroundColor Yellow
        Write-Host ""
        
        # Show last 20 lines, filtering out GET requests to reduce noise
        Get-Content $latestLog.FullName -Tail 30 | Where-Object { $_ -notmatch "GET /" -and $_ -notmatch "404 -" } | Select-Object -Last 20
    } else {
        Write-Host "No log files found." -ForegroundColor Red
    }
    Write-Host ""
}

# Main script logic
switch ($Command.ToLower()) {
    "start" { Start-Services }
    "stop" { Stop-Services }
    "restart" { Restart-Services }
    "status" { Show-Status }
    "logs" { Show-Logs }
    "help" { Show-Help }
    default { Show-Help }
}
