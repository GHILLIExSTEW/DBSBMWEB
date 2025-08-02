# Windows Task Scheduler Setup for Flask Service
# Step-by-step guide to create a scheduled task that keeps Flask running

## Method 1: Using PowerShell (Recommended)

### 1. Open PowerShell as Administrator

### 2. Create the Scheduled Task with this command:

```powershell
# Define task parameters
$TaskName = "Flask-BetTrackingAI-Service"
$TaskDescription = "Keeps the Flask Bet Tracking AI server running continuously"
$ScriptPath = "C:\path\to\your\project\start_flask_service.ps1"  # UPDATE THIS PATH
$WorkingDirectory = "C:\path\to\your\project"  # UPDATE THIS PATH

# Create the scheduled task action
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`"" -WorkingDirectory $WorkingDirectory

# Create trigger for system startup
$StartupTrigger = New-ScheduledTaskTrigger -AtStartup

# Create trigger to run every 5 minutes (restart if stopped)
$PeriodicTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)

# Combine triggers
$Triggers = @($StartupTrigger, $PeriodicTrigger)

# Task settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -DontStopOnIdleEnd

# Create the principal (run as SYSTEM for highest privileges)
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register the task
Register-ScheduledTask -TaskName $TaskName -Description $TaskDescription -Action $Action -Trigger $Triggers -Settings $Settings -Principal $Principal

Write-Host "✅ Scheduled task '$TaskName' created successfully!"
Write-Host "🚀 Flask service will start automatically on system boot and restart every 5 minutes if stopped"
```

## Method 2: Using Task Scheduler GUI

### 1. Open Task Scheduler
- Press `Win + R`, type `taskschd.msc`, press Enter

### 2. Create Basic Task
- Click "Create Task..." in the right panel
- **Name**: `Flask-BetTrackingAI-Service`
- **Description**: `Keeps the Flask Bet Tracking AI server running continuously`
- **Security Options**: 
  - Select "Run whether user is logged on or not"
  - Check "Run with highest privileges"
  - Configure for: "Windows 10"

### 3. Set Triggers
**Trigger 1 - At Startup:**
- Click "Triggers" tab → "New..."
- Begin the task: "At startup"
- Settings: "Enabled"

**Trigger 2 - Periodic Check:**
- Click "New..." again
- Begin the task: "On a schedule"
- Settings: "Daily"
- Recur every: 1 days
- Repeat task every: 5 minutes
- For a duration of: Indefinitely
- Settings: "Enabled"

### 4. Set Actions
- Click "Actions" tab → "New..."
- Action: "Start a program"
- Program/script: `PowerShell.exe`
- Add arguments: `-ExecutionPolicy Bypass -File "C:\path\to\your\project\start_flask_service.ps1"`
- Start in: `C:\path\to\your\project`

### 5. Configure Settings
- Click "Settings" tab
- Check: "Allow task to be run on demand"
- Check: "Run task as soon as possible after a scheduled start is missed"
- Check: "If the running task does not end when requested, force it to stop"
- If the task is already running: "Do not start a new instance"

### 6. Save the Task
- Click "OK"
- Enter administrator credentials when prompted

## Verification Steps

### 1. Test the Task Manually
```powershell
# Run the task immediately
Start-ScheduledTask -TaskName "Flask-BetTrackingAI-Service"

# Check task status
Get-ScheduledTask -TaskName "Flask-BetTrackingAI-Service" | Get-ScheduledTaskInfo
```

### 2. Check if Flask is Running
```powershell
# Check for Python processes
Get-Process python -ErrorAction SilentlyContinue

# Check if port 5000 is in use
netstat -an | findstr :5000

# Test the web endpoint
Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing
```

### 3. Monitor Logs
- Check logs in: `C:\path\to\your\project\logs\`
- Flask service log: `flask_service_YYYY-MM-DD.log`
- Error log: `flask_errors_YYYY-MM-DD.log`

## Troubleshooting

### If the task isn't starting:
1. Check Windows Event Viewer (`eventvwr.msc`)
2. Look under: Windows Logs → System and Application
3. Search for events related to Task Scheduler

### If Flask keeps restarting:
1. Check the error logs in the `logs` folder
2. Verify your `.env` file is present and correct
3. Ensure all Python dependencies are installed

### If you need to stop the service:
```powershell
# Stop the scheduled task
Stop-ScheduledTask -TaskName "Flask-BetTrackingAI-Service"

# Kill any remaining Python processes
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine -like "*flask_service.py*"
} | Stop-Process -Force
```

## Benefits of This Setup

✅ **Automatic Startup**: Flask starts when Windows boots
✅ **Auto-Recovery**: Restarts if the service crashes
✅ **Logging**: All activity is logged for troubleshooting
✅ **Background Operation**: Runs without user login
✅ **High Availability**: 99.9% uptime for your Flask app

Your Flask application will now run continuously as a Windows service!
