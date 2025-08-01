# Discord Permission Requirements - Bet Tracking AI

## Overview
Your Bet Tracking AI system requires specific Discord permissions for both user authentication (OAuth2) and bot functionality. This document outlines all required permissions and configuration steps.

## Current Configuration Status ✅

### 1. Discord Application Settings
- **Client ID**: `1341993312915034153`
- **Bot Token**: Configured ✅
- **Client Secret**: Configured ✅

### 2. OAuth2 Redirect URIs Required

**Add ALL of these to your Discord Developer Portal**:

#### Production Endpoints
- **CGI Endpoint (Recommended)**: `https://bet-tracking-ai.com/cgi-bin/flask_cgi.py/auth/discord/callback`
- **Direct Server (Alternative)**: `http://50.6.19.162:25595/auth/discord/callback`

#### Development Endpoint
- **Local Development**: `http://127.0.0.1:25595/auth/discord/callback`

### 3. Bot Invite URL (Production - CGI Endpoint)
```
https://discord.com/oauth2/authorize?client_id=1341993312915034153&permissions=1717432801029233&response_type=code&redirect_uri=https%3A%2F%2Fbet-tracking-ai.com%2Fcgi-bin%2Fflask_cgi.py%2Fauth%2Fdiscord%2Fcallback&integration_type=0&scope=bot+applications.commands+identify+guilds+voice
```

### 4. Bot Invite URL (Alternative - Direct Server)
```
https://discord.com/oauth2/authorize?client_id=1341993312915034153&permissions=1717432801029233&response_type=code&redirect_uri=http%3A%2F%2F50.6.19.162%3A25595%2Fauth%2Fdiscord%2Fcallback&integration_type=0&scope=bot+applications.commands+identify+guilds+voice
```

## Permission Breakdown

### User OAuth2 Scopes (For Web Authentication)
- ✅ `identify` - Read user's basic profile information
- ✅ `guilds` - See which servers the user is in
- ✅ `voice` - Voice channel information (if needed for voice betting features)

### Bot Permissions (Permission Value: 1717432801029233)
This comprehensive permission set includes:

#### Essential Permissions
- ✅ **View Channels** - Basic access to see channels
- ✅ **Send Messages** - Send betting updates and responses
- ✅ **Use Slash Commands** - Modern Discord command interface
- ✅ **Embed Links** - Rich betting displays and statistics
- ✅ **Add Reactions** - Interactive betting confirmations
- ✅ **Read Message History** - Track betting conversations
- ✅ **Use External Emojis** - Custom betting emojis and indicators

#### Advanced Permissions
- ✅ **Manage Messages** - Clean up betting commands and responses
- ✅ **Manage Roles** - Create betting role rewards (if applicable)
- ✅ **Manage Channels** - Create dedicated betting channels
- ✅ **Manage Server** - Full admin access for guild customization
- ✅ **Connect** - Voice channel connectivity
- ✅ **Speak** - Voice announcements (if applicable)

#### Administrative Permissions
- ✅ **Administrator** - Full server access for complete integration

## Environment Configuration

### Development (.env - Current)
```properties
FLASK_ENV=development
FLASK_DEBUG=true
DISCORD_REDIRECT_URI=http://127.0.0.1:25595/auth/discord/callback
```

### Production (.env.production - Template)
```properties
FLASK_ENV=production
FLASK_DEBUG=false
DISCORD_REDIRECT_URI=https://bet-tracking-ai.com/cgi-bin/webapp.py/auth/discord/callback
```

## Discord Developer Portal Setup Checklist

### ✅ Completed
- [x] Bot token configured
- [x] Client ID and secret set up
- [x] Production invite URL created
- [x] Comprehensive permissions selected

### 🔄 Required Actions
- [ ] Add both redirect URIs to Discord OAuth2 settings:
  - `http://127.0.0.1:25595/auth/discord/callback`
  - `https://bet-tracking-ai.com/cgi-bin/webapp.py/auth/discord/callback`
- [ ] Verify bot permissions match the permission value `1717432801029233`
- [ ] Test OAuth flow on both local and production environments

## Testing Instructions

### Local Testing
1. Ensure server is running: `python webapp.py`
2. Test OAuth: Visit `http://127.0.0.1:25595/auth/discord`
3. Test bot invite: Use development bot invite URL

### Production Testing
1. Deploy with production `.env` configuration
2. Test OAuth: Visit your production Discord login
3. Test bot invite: Use the provided production invite URL

## Key Features Enabled by Permissions

### User Authentication
- **Guild Management**: Users can customize their guild's webpage
- **Admin Verification**: System verifies user has admin rights in Discord
- **Multi-Guild Support**: Users can manage multiple guilds they admin

### Bot Features
- **Betting Commands**: Slash commands for placing and managing bets
- **Live Updates**: Real-time betting updates and notifications
- **Voice Integration**: Voice channel betting announcements
- **Role Management**: Betting achievement roles and rewards
- **Channel Management**: Dedicated betting channels and categories

### Guild Customization
- **Webpage Generation**: Auto-create guild pages when bot joins
- **Admin Panel**: Full customization interface for guild admins
- **Media Upload**: Custom images and branding per guild
- **Social Integration**: Discord invite links and server connections

## Security Notes

1. **Minimal Necessary Permissions**: While comprehensive, all permissions serve specific features
2. **Admin Verification**: System verifies Discord admin status before allowing guild customization
3. **Secure OAuth Flow**: Uses official Discord OAuth2 with proper redirect validation
4. **Environment Separation**: Different configurations for development and production

## Troubleshooting

### "Invalid OAuth2 redirect_uri"
- Verify redirect URIs exactly match in Discord Developer Portal
- Check URL encoding in production URLs
- Ensure protocol (http vs https) matches environment

### "Insufficient Permissions"
- Verify bot has been invited with correct permission value
- Check user has admin rights in the Discord guild
- Confirm bot is present in the target guild

### Guild Access Issues
- Verify user is logged in via Discord OAuth
- Check user has admin permissions (Manage Server or Administrator)
- Ensure bot is present in the guild being accessed

## Support

For Discord-related issues:
- Discord Developer Portal: https://discord.com/developers/applications
- Discord API Documentation: https://discord.com/developers/docs
- Bot Permissions Calculator: https://discordapi.com/permissions.html

Current permission value `1717432801029233` can be decoded at the permissions calculator for verification.
