# Flask Service Launcher for Windows Task Scheduler
# This script ensures the Flask app runs continuously

# Set the working directory
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptPath

# Create log directory if it doesn't exist
$LogDir = Join-Path $ScriptPath "logs"
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force
}

# Define log files
$LogFile = Join-Path $LogDir "flask_service_$(Get-Date -Format 'yyyy-MM-dd').log"
$ErrorLog = Join-Path $LogDir "flask_errors_$(Get-Date -Format 'yyyy-MM-dd').log"

# Function to write timestamped log
function Write-Log {
    param($Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "$Timestamp - $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

# Function to check if Flask is already running
function Test-FlaskRunning {
    $FlaskProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -eq "python" -and 
        (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine -like "*flask_service.py*"
    }
    return $FlaskProcess -ne $null
}

# Main execution
try {
    Write-Log "🚀 Flask Service Launcher Starting..."
    
    # Check if Flask is already running
    if (Test-FlaskRunning) {
        Write-Log "⚠️ Flask service is already running. Skipping startup."
        exit 0
    }
    
    # Ensure Python is available
    try {
        $PythonVersion = & python --version 2>&1
        Write-Log "📍 Using Python: $PythonVersion"
    }
    catch {
        Write-Log "❌ Python not found in PATH. Please install Python or add it to PATH."
        exit 1
    }
    
    # Start the Flask service
    Write-Log "🔄 Starting Flask service in background..."
    
    $ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
    $ProcessInfo.FileName = "python"
    $ProcessInfo.Arguments = "flask_service.py service"
    $ProcessInfo.WorkingDirectory = $ScriptPath
    $ProcessInfo.UseShellExecute = $false
    $ProcessInfo.RedirectStandardOutput = $true
    $ProcessInfo.RedirectStandardError = $true
    $ProcessInfo.CreateNoWindow = $true
    
    $Process = New-Object System.Diagnostics.Process
    $Process.StartInfo = $ProcessInfo
    
    # Event handlers for output
    $Process.add_OutputDataReceived({
        param($sender, $e)
        if ($e.Data -ne $null) {
            Add-Content -Path $LogFile -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - STDOUT: $($e.Data)"
        }
    })
    
    $Process.add_ErrorDataReceived({
        param($sender, $e)
        if ($e.Data -ne $null) {
            Add-Content -Path $ErrorLog -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - STDERR: $($e.Data)"
        }
    })
    
    # Start the process
    $Process.Start()
    $Process.BeginOutputReadLine()
    $Process.BeginErrorReadLine()
    
    Write-Log "✅ Flask service started with PID: $($Process.Id)"
    Write-Log "🌐 Flask app should be accessible at: http://YOUR_LIGHTSAIL_IP:5000"
    Write-Log "📝 Logs are being written to: $LogFile"
    
    # Don't wait for the process to exit (let it run in background)
    Write-Log "🎯 Flask service is now running as background process"
    
}
catch {
    Write-Log "💥 Error starting Flask service: $($_.Exception.Message)"
    Add-Content -Path $ErrorLog -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - LAUNCHER ERROR: $($_.Exception.Message)"
    exit 1
}
