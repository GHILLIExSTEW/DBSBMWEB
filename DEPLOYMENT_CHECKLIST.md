# Production Deployment Checklist

## Pre-Deployment Setup

### 1. Discord Developer Portal Configuration
- [ ] Go to https://discord.com/developers/applications/1341993312915034153
- [ ] OAuth2 → General → Add Redirect URIs:
  - [ ] `https://bet-tracking-ai.com/cgi-bin/flask_cgi.py/auth/discord/callback` (CGI)
  - [ ] `http://50.6.19.162:25595/auth/discord/callback` (Direct server)
  - [ ] `http://127.0.0.1:25595/auth/discord/callback` (Local dev)

### 2. Environment Configuration
- [ ] Copy `.env.production` to `.env`
- [ ] Choose redirect URI approach (CGI recommended)
- [ ] Verify database credentials

### 3. File Upload to Production Server
- [ ] Upload `flask_cgi.py` to cgi-bin directory
- [ ] Upload `webapp.py` (main Flask app)
- [ ] Upload `.env` (production config)
- [ ] Upload `bot/` directory (templates/static)
- [ ] Upload all Python dependencies
- [ ] Set executable permissions: `chmod +x flask_cgi.py`

## Testing Production Deployment

### CGI Endpoint Testing
- [ ] Health check: `https://bet-tracking-ai.com/cgi-bin/flask_cgi.py/health`
- [ ] Main page: `https://bet-tracking-ai.com/cgi-bin/flask_cgi.py/`
- [ ] Subscriptions: `https://bet-tracking-ai.com/cgi-bin/flask_cgi.py/subscriptions`
- [ ] Server list: `https://bet-tracking-ai.com/cgi-bin/flask_cgi.py/server-list`
- [ ] Discord OAuth: `https://bet-tracking-ai.com/cgi-bin/flask_cgi.py/auth/discord`

### Direct Server Testing (Alternative)
- [ ] Start server: `python webapp.py` on port 25595
- [ ] Health check: `http://50.6.19.162:25595/health`
- [ ] Main page: `http://50.6.19.162:25595/`
- [ ] Discord OAuth: `http://50.6.19.162:25595/auth/discord`

### Guild Features Testing
- [ ] Public guild page: `/guild/123456789/public`
- [ ] Guild customization: `/guild/123456789/customize`
- [ ] Demo mode functionality
- [ ] Error handling

## Database Setup (Optional - for full features)

- [ ] Connect to MySQL: `na05-sql.pebblehost.com`
- [ ] Run guild customization schema
- [ ] Test database connectivity
- [ ] Verify table creation

## Discord Bot Integration

- [ ] Test bot invite from subscription page
- [ ] Verify bot permissions
- [ ] Test OAuth flow end-to-end
- [ ] Confirm guild admin detection

## Production Monitoring

- [ ] Check server error logs
- [ ] Monitor response times
- [ ] Verify HTTPS functionality
- [ ] Test from different devices/networks

## Current Status

### ✅ Completed
- [x] Updated flask_cgi.py for production
- [x] Updated subscription page with correct invite URL
- [x] Created production environment configuration
- [x] Updated Discord permissions documentation
- [x] Created deployment guides

### 🔄 Next Steps
- [ ] Deploy files to production server
- [ ] Update Discord Developer Portal settings
- [ ] Test production endpoints
- [ ] Setup database tables (for full features)

## Quick Commands

### Copy Production Config
```bash
cp .env.production .env
```

### Set CGI Permissions
```bash
chmod +x flask_cgi.py
```

### Test Database Connection
```bash
mysql -h na05-sql.pebblehost.com -u customer_990306_Server_database -p
```

### View Logs
```bash
tail -f db_logs/webapp_daily.log
```

## Support Contacts

- **Discord API Issues**: Discord Developer Portal
- **Server Issues**: Hosting provider support
- **Database Issues**: Database admin panel
- **Application Issues**: Check error logs and health endpoints
