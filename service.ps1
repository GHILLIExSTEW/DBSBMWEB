# Flask Server Auto-Restart PowerShell Service
# This script ensures the Flask server never stays down

param(
    [string]$Action = "start"
)

$ServiceName = "FlaskWatchdog"
$WorkingDir = "c:\Users\Administrator\Desktop\DBSBMWEB"
$PythonExe = "C:/Users/Administrator/Desktop/DBSBMWEB/.venv/Scripts/python.exe"
$WatchdogScript = "watchdog.py"
$LogFile = "cgi-bin\db_logs\powershell_service.log"

function Write-ServiceLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $LogFile -Append
    Write-Host "$timestamp - $Message"
}

function Start-FlaskService {
    Write-ServiceLog "Starting Flask Auto-Restart Service..."
    
    Set-Location $WorkingDir
    
    # Ensure logs directory exists
    if (!(Test-Path "cgi-bin\db_logs")) {
        New-Item -ItemType Directory -Path "cgi-bin\db_logs" -Force
    }
    
    while ($true) {
        try {
            Write-ServiceLog "Starting watchdog process..."
            
            # Start the watchdog
            $process = Start-Process -FilePath $PythonExe -ArgumentList $WatchdogScript -WorkingDirectory $WorkingDir -PassThru -WindowStyle Hidden
            
            Write-ServiceLog "Watchdog started with PID: $($process.Id)"
            
            # Wait for the process to exit
            $process.WaitForExit()
            
            Write-ServiceLog "Watchdog process exited unexpectedly (Exit Code: $($process.ExitCode))"
            Write-ServiceLog "Restarting watchdog in 5 seconds..."
            
            Start-Sleep -Seconds 5
            
        } catch {
            Write-ServiceLog "Error starting watchdog: $($_.Exception.Message)"
            Write-ServiceLog "Retrying in 10 seconds..."
            Start-Sleep -Seconds 10
        }
    }
}

function Stop-FlaskService {
    Write-ServiceLog "Stopping Flask Service..."
    
    # Kill all python processes (watchdog and flask server)
    Get-Process -Name "python" -ErrorAction SilentlyContinue | ForEach-Object {
        Write-ServiceLog "Stopping Python process PID: $($_.Id)"
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    
    Write-ServiceLog "Flask Service stopped"
}

function Get-FlaskServiceStatus {
    $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
    $listeningPort = netstat -an | Select-String ":25595.*LISTENING"
    
    if ($pythonProcesses -and $listeningPort) {
        Write-ServiceLog "Flask Service is RUNNING"
        Write-ServiceLog "Python processes: $($pythonProcesses.Count)"
        Write-ServiceLog "Port 25595 is listening"
        return $true
    } else {
        Write-ServiceLog "Flask Service is NOT RUNNING"
        return $false
    }
}

# Main execution
switch ($Action.ToLower()) {
    "start" {
        Start-FlaskService
    }
    "stop" {
        Stop-FlaskService
    }
    "restart" {
        Stop-FlaskService
        Start-Sleep -Seconds 3
        Start-FlaskService
    }
    "status" {
        Get-FlaskServiceStatus
    }
    default {
        Write-Host "Usage: .\service.ps1 -Action [start|stop|restart|status]"
        Write-Host "Example: .\service.ps1 -Action start"
    }
}
