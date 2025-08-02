# Ultra-Reliable Flask Server Manager
# This PowerShell script will keep your Flask server running 24/7

param(
    [string]$Action = "start"
)

$Config = @{
    PythonExe = "C:/Users/Administrator/Desktop/DBSBMWEB/.venv/Scripts/python.exe"
    FlaskScript = "c:\Users\Administrator\Desktop\DBSBMWEB\cgi-bin\production_server.py"
    WorkingDir = "c:\Users\Administrator\Desktop\DBSBMWEB\cgi-bin"
    HealthUrl = "http://localhost:25595/health"
    LogFile = "c:\Users\Administrator\Desktop\DBSBMWEB\cgi-bin\db_logs\powershell_autostart.log"
    CheckInterval = 15
    RestartDelay = 5
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $Message"
    Write-Host $logMessage
    $logMessage | Out-File -FilePath $Config.LogFile -Append -Encoding UTF8
}

function Test-ServerHealth {
    try {
        $response = Invoke-WebRequest -Uri $Config.HealthUrl -TimeoutSec 5 -UseBasicParsing
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Stop-AllPythonProcesses {
    try {
        Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Write-Log "Stopped all Python processes"
    } catch {
        Write-Log "Error stopping Python processes: $($_.Exception.Message)"
    }
}

function Start-FlaskServer {
    try {
        Write-Log "Starting Flask server..."
        
        # Stop any existing processes first
        Stop-AllPythonProcesses
        
        # Start new Flask server
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = $Config.PythonExe
        $processInfo.Arguments = $Config.FlaskScript
        $processInfo.WorkingDirectory = $Config.WorkingDir
        $processInfo.UseShellExecute = $false
        $processInfo.CreateNoWindow = $true
        
        $process = [System.Diagnostics.Process]::Start($processInfo)
        
        if ($process) {
            Write-Log "Flask server started with PID: $($process.Id)"
            
            # Wait for server to start
            Start-Sleep -Seconds 8
            
            # Test if server is responding
            $healthyAttempts = 0
            for ($i = 0; $i -lt 6; $i++) {
                if (Test-ServerHealth) {
                    $healthyAttempts++
                    if ($healthyAttempts -ge 2) {
                        Write-Log "Server is healthy and responding"
                        return $true
                    }
                }
                Start-Sleep -Seconds 2
            }
            
            Write-Log "Server started but not responding to health checks"
            return $false
        } else {
            Write-Log "Failed to start Flask server process"
            return $false
        }
    } catch {
        Write-Log "Error starting Flask server: $($_.Exception.Message)"
        return $false
    }
}

function Start-MonitoringLoop {
    Write-Log "=== Starting Flask Auto-Restart Service ==="
    Write-Log "Monitoring URL: $($Config.HealthUrl)"
    Write-Log "Check interval: $($Config.CheckInterval) seconds"
    
    # Ensure logs directory exists
    $logDir = Split-Path $Config.LogFile -Parent
    if (!(Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    # Initial server start
    if (!(Start-FlaskServer)) {
        Write-Log "Failed to start server initially - retrying in $($Config.RestartDelay) seconds"
        Start-Sleep -Seconds $Config.RestartDelay
    }
    
    # Monitoring loop
    $consecutiveFailures = 0
    $lastHealthCheck = Get-Date
    
    while ($true) {
        try {
            $currentTime = Get-Date
            
            # Check server health
            if (Test-ServerHealth) {
                if ($consecutiveFailures -gt 0) {
                    Write-Log "Server recovered after $consecutiveFailures failures"
                    $consecutiveFailures = 0
                }
                $lastHealthCheck = $currentTime
            } else {
                $consecutiveFailures++
                $timeSinceLastHealthy = ($currentTime - $lastHealthCheck).TotalMinutes
                
                Write-Log "Health check failed (failure #$consecutiveFailures, $([math]::Round($timeSinceLastHealthy, 1)) min since last healthy)"
                
                # Restart after 2 consecutive failures or 5 minutes without response
                if ($consecutiveFailures -ge 2 -or $timeSinceLastHealthy -gt 5) {
                    Write-Log "Restarting server due to health check failures"
                    
                    if (Start-FlaskServer) {
                        $consecutiveFailures = 0
                        $lastHealthCheck = Get-Date
                    } else {
                        Write-Log "Server restart failed - waiting $($Config.RestartDelay) seconds before retry"
                        Start-Sleep -Seconds $Config.RestartDelay
                    }
                }
            }
            
            # Wait before next check
            Start-Sleep -Seconds $Config.CheckInterval
            
        } catch {
            Write-Log "Error in monitoring loop: $($_.Exception.Message)"
            Start-Sleep -Seconds $Config.CheckInterval
        }
    }
}

function Get-ServiceStatus {
    $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
    $portListening = netstat -an | Select-String ":25595.*LISTENING"
    $serverHealthy = Test-ServerHealth
    
    Write-Log "=== Flask Service Status ==="
    Write-Log "Python processes running: $($pythonProcesses.Count)"
    Write-Log "Port 25595 listening: $($portListening -ne $null)"
    Write-Log "Server responding to health checks: $serverHealthy"
    
    if ($pythonProcesses -and $portListening -and $serverHealthy) {
        Write-Log "✅ Flask Service is RUNNING and HEALTHY"
        return $true
    } else {
        Write-Log "❌ Flask Service is NOT RUNNING or UNHEALTHY"
        return $false
    }
}

# Main execution
switch ($Action.ToLower()) {
    "start" {
        Start-MonitoringLoop
    }
    "stop" {
        Write-Log "Stopping Flask Service..."
        Stop-AllPythonProcesses
        Write-Log "Flask Service stopped"
    }
    "restart" {
        Write-Log "Restarting Flask Service..."
        Stop-AllPythonProcesses
        Start-Sleep -Seconds 3
        Start-FlaskServer
    }
    "status" {
        Get-ServiceStatus
    }
    default {
        Write-Host "Usage: .\ultra_reliable.ps1 -Action [start|stop|restart|status]"
        Write-Host ""
        Write-Host "Examples:"
        Write-Host "  .\ultra_reliable.ps1 -Action start     # Start monitoring service"
        Write-Host "  .\ultra_reliable.ps1 -Action stop      # Stop all Flask processes"
        Write-Host "  .\ultra_reliable.ps1 -Action status    # Check service status"
        Write-Host "  .\ultra_reliable.ps1 -Action restart   # Restart Flask server"
    }
}
