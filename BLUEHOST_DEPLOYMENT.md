# Bluehost Deployment Guide
**Bet Tracking AI - Production Deployment**

## Overview
This guide walks you through deploying your Flask application on Bluehost using the files we've created.

## Pre-Deployment Checklist

### 1. Upload Files to Bluehost
Upload the entire project to your Bluehost account:
```
- Upload all files to your domain root (public_html)
- Ensure the cgi-bin/ directory is in the correct location
- Verify file permissions (755 for directories, 644 for files)
```

### 2. Configure Environment
Your `.env.bluehost` file contains all production settings. Update these values:

```env
# Database Configuration (from Pebblehost)
MYSQL_HOST=your.pebblehost.database.url
MYSQL_USER=your_db_username
MYSQL_PASSWORD=your_db_password
MYSQL_DB=your_database_name
MYSQL_PORT=3306

# Discord OAuth (from Discord Developer Portal)
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_REDIRECT_URI=https://bet-tracking-ai.com:25595/auth/callback
DISCORD_BOT_TOKEN=your_bot_token

# Flask Configuration
SECRET_KEY=your_super_secure_secret_key_here
DEBUG=False
FLASK_ENV=production

# Server Configuration
HOST=0.0.0.0
PORT=25595
```

### 3. Install Dependencies
Connect to your Bluehost account via SSH and run:
```bash
cd /home/username/public_html
python3 -m pip install --user -r requirements.txt
```

## Deployment Steps

### Step 1: Environment Check
Run the health check script to verify everything is configured:
```bash
python3 check_bluehost.py
```

This will test:
- ✅ Python version compatibility
- ✅ Required dependencies
- ✅ File structure
- ✅ Database connection
- ✅ Discord configuration

### Step 2: Start the Server
Use the startup script we created:
```bash
python3 start_bluehost.py
```

This script will:
1. Set up the Python environment
2. Install any missing dependencies
3. Verify all files are in place
4. Start the Flask server on port 25595

### Step 3: Configure Cloudflare
In your Cloudflare dashboard:

1. **DNS Settings:**
   - A record: `bet-tracking-ai.com` → Your Bluehost IP
   - CNAME: `www` → `bet-tracking-ai.com`

2. **SSL/TLS Settings:**
   - SSL/TLS encryption mode: "Full (strict)"
   - Edge Certificates: Enable "Always Use HTTPS"

3. **Page Rules:**
   - URL: `http://bet-tracking-ai.com/*`
   - Setting: "Always Use HTTPS"

### Step 4: Test Your Deployment
Visit these URLs to verify everything works:

1. **Landing Page:** `https://bet-tracking-ai.com:25595/`
2. **Subscriptions:** `https://bet-tracking-ai.com:25595/subscriptions`
3. **Discord Auth:** `https://bet-tracking-ai.com:25595/auth/discord`
4. **Health Check:** `https://bet-tracking-ai.com:25595/health`

## Directory Structure
Your final structure should look like:
```
public_html/
├── .env.bluehost              # Production environment config
├── start_bluehost.py          # Server startup script
├── check_bluehost.py          # Environment health check
├── requirements.txt           # Python dependencies
├── index.html                 # Static landing page
├── cgi-bin/
│   ├── webapp.py             # Main Flask application
│   ├── bot/
│   │   ├── templates/        # Jinja2 templates
│   │   │   ├── subscription_landing.html
│   │   │   ├── guild_customize.html
│   │   │   ├── guild_public.html
│   │   │   └── error.html
│   │   └── static/           # CSS, JS, images
│   │       ├── css/
│   │       ├── js/
│   │       ├── images/
│   │       └── guild_images/
│   └── db_logs/              # Application logs
└── docs/                     # Documentation
```

## Available Pages and Features

### 1. Subscription Landing (`/subscriptions`)
- Modern pricing tiers (Free, Standard, Premium, Enterprise)
- Discord OAuth integration
- User role-based access

### 2. Guild Customization (`/guild/<guild_id>/customize`)
- Admin-only access for guild administrators
- Customizable colors, logos, content
- Live preview functionality
- Demo mode for testing

### 3. Public Guild Pages (`/guild/<guild_id>`)
- Customized public pages for each Discord server
- Live scores and betting data
- Branded with guild-specific styling

### 4. Admin Features
- Server management dashboard
- User subscription tracking
- Custom guild webpage generation
- Demo mode for testing without affecting live data

## Environment Variables Explained

### Database Settings
- `MYSQL_HOST`: Your Pebblehost database URL
- `MYSQL_USER`: Database username
- `MYSQL_PASSWORD`: Database password
- `MYSQL_DB`: Database name

### Discord OAuth
- `DISCORD_CLIENT_ID`: From Discord Developer Portal
- `DISCORD_CLIENT_SECRET`: From Discord Developer Portal
- `DISCORD_REDIRECT_URI`: Callback URL for OAuth
- `DISCORD_BOT_TOKEN`: Bot token for API access

### Flask Settings
- `SECRET_KEY`: Used for session encryption (change this!)
- `DEBUG`: Set to False for production
- `FLASK_ENV`: Set to production

## Troubleshooting

### Common Issues

1. **500 Internal Server Error**
   - Check Python path and permissions
   - Verify all dependencies are installed
   - Check error logs in `cgi-bin/db_logs/`

2. **Database Connection Failed**
   - Verify Pebblehost database credentials
   - Check if your Bluehost IP is whitelisted
   - Test connection with MySQL client

3. **Discord OAuth Not Working**
   - Verify redirect URI matches exactly
   - Check client ID and secret are correct
   - Ensure bot has proper permissions

4. **Port 25595 Not Accessible**
   - Contact Bluehost support to enable custom ports
   - Consider using a subdomain instead
   - Check firewall settings

### Log Files
Check these locations for error information:
- `cgi-bin/db_logs/webapp_daily.log`
- Bluehost error logs in cPanel
- Browser developer console for frontend errors

## Security Notes

- Never commit `.env.bluehost` to version control
- Use strong, unique passwords for all services
- Enable two-factor authentication on all accounts
- Regularly update dependencies
- Monitor access logs for suspicious activity

## Support
If you encounter issues:
1. Run the health check script first
2. Check the troubleshooting section
3. Review log files for specific errors
4. Test individual components (database, Discord auth, etc.)

## Next Steps After Deployment
1. Set up automated backups
2. Configure monitoring and alerts
3. Set up SSL certificate renewal
4. Plan for scaling if user base grows
5. Implement additional security measures
