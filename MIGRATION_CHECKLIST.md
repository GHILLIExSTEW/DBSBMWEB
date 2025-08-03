# VPS Migration Checklist and Setup Guide

## 🚀 Pre-Migration Checklist

### ✅ Environment Setup
- [ ] Created `.env` file in `cgi-bin/` directory
- [ ] Updated all environment variables with VPS-specific values
- [ ] Generated strong SECRET_KEY
- [ ] Configured domain/IP settings

### ✅ Database Setup
- [ ] Install MySQL/MariaDB on VPS
- [ ] Create database user and database
- [ ] Import existing database schema/data (if migrating)
- [ ] Test database connection

### ✅ Discord Configuration
- [ ] Update Discord OAuth redirect URI in Discord Developer Portal
- [ ] Test Discord OAuth flow with new domain
- [ ] Verify bot permissions and guild access

### ✅ Dependencies
- [ ] Install Python dependencies (`pip install -r requirements.txt`)
- [ ] Install Redis (optional but recommended)
- [ ] Test all imports and dependencies

### ✅ Service Configuration
- [ ] Set up Flask as Windows service
- [ ] Configure auto-start on boot
- [ ] Test service startup and restart
- [ ] Configure logging directory permissions

### ✅ Network Configuration
- [ ] Configure Windows Firewall for ports 80, 5000
- [ ] Set up port forwarding/proxy if needed
- [ ] Configure domain DNS to point to VPS IP
- [ ] Test external access

## 🛠️ Migration Commands

### 1. Install Dependencies
```cmd
cd C:\Users\Administrator\Desktop\Bot+Server\DBSBMWEB
pip install -r requirements.txt
```

### 2. Test Database Connection
```cmd
cd cgi-bin
python test_database.py
```

### 3. Test Flask Application
```cmd
python flask_service.py test
```

### 4. Start Service (Development)
```cmd
python flask_service.py service
```

### 5. Set up Windows Service (Production)
```cmd
# Run as Administrator
setup_autostart.bat
```

## 🔧 Configuration Updates Needed

### `.env` File Updates
1. **SECRET_KEY**: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
2. **MYSQL_PASSWORD**: Set your MySQL root password
3. **DISCORD_CLIENT_ID/SECRET**: From Discord Developer Portal
4. **DISCORD_REDIRECT_URI**: Update to your VPS domain
5. **DOMAIN**: Set to your VPS IP or domain

### Discord Developer Portal Updates
1. Go to https://discord.com/developers/applications
2. Select your application
3. Go to OAuth2 → General
4. Update Redirect URIs to include: `http://your-vps-domain.com/discord/callback`

### Database Setup Commands
```sql
-- Create database and user
CREATE DATABASE dbsbm;
CREATE USER 'dbsbm'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON dbsbm.* TO 'dbsbm'@'localhost';
FLUSH PRIVILEGES;
```

## 🚨 Post-Migration Verification

### Test Points
- [ ] Flask application starts without errors
- [ ] Database connection successful
- [ ] Discord OAuth login works
- [ ] Guild pages load correctly
- [ ] Static files (CSS, JS, images) serve properly
- [ ] Logging is working and files are created
- [ ] Service restarts automatically on failure

### URLs to Test
- http://your-domain:5000/ (Landing page)
- http://your-domain:5000/discord/login (OAuth)
- http://your-domain:5000/guild/test-guild-id (Guild page)
- http://your-domain:5000/live-scores (Sports data)

## 🔍 Troubleshooting

### Common Issues
1. **Port 5000 in use**: Change WEBAPP_PORT in .env
2. **Database connection failed**: Check MySQL service and credentials
3. **Discord OAuth error**: Verify redirect URI matches exactly
4. **Static files 404**: Check file permissions and paths
5. **Service won't start**: Check Windows Event Viewer for errors

### Log Locations
- Flask Service: `flask_service.log`
- Web Application: `db_logs/webapp_daily.log`
- Windows Service: Windows Event Viewer → Application logs

## 📝 Migration Notes
- Original setup expects domain: `bet-tracker-pro.com`
- Service runs on port 5000 by default
- Supports Cloudflare proxy (ProxyFix enabled)
- Uses daily rotating logs
- Auto-restart capability built-in
