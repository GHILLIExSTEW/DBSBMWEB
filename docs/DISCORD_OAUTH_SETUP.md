# Discord OAuth Setup Instructions

## Overview
The webapp now includes Discord OAuth authentication to verify that users are members of Discord servers that have your bot installed. This ensures only authorized users can access guild-specific data.

## Setup Steps

### 1. Create Discord Application (if not already done)
1. Go to https://discord.com/developers/applications
2. Click "New Application" and give it a name
3. Note down the **Application ID** (this is your CLIENT_ID)

### 2. Get OAuth Credentials
1. In your Discord application, go to the "OAuth2" section
2. Copy the **Client Secret** (keep this private!)
3. Add the redirect URI: `http://127.0.0.1:25594/auth/discord/callback` for local development
   - For production, use your actual domain: `https://yourdomain.com/auth/discord/callback`

### 3. Update .env File
Update your `.env` file with the Discord credentials:

```env
# Discord OAuth Configuration
DISCORD_CLIENT_ID=your_actual_discord_bot_client_id
DISCORD_CLIENT_SECRET=your_actual_discord_bot_client_secret
DISCORD_REDIRECT_URI=http://127.0.0.1:25594/auth/discord/callback
DISCORD_BOT_TOKEN=your_actual_discord_bot_token
```

### 4. How It Works

#### User Flow:
1. **Unauthenticated users** see the subscription landing page with a "Login with Discord" button
2. **Authenticated users** with no accessible guilds see the subscription page with their username
3. **Authenticated users** with accessible guilds see the main dashboard

#### Access Control:
- Users must login with Discord to access guild-specific data
- The system checks which Discord servers the user is a member of
- It then cross-references with servers where your bot is installed
- Only users in servers with the bot can access that server's data

#### Routes:
- `/auth/discord` - Initiates Discord OAuth login
- `/auth/discord/callback` - Handles OAuth callback
- `/auth/logout` - Logs out the user
- All guild routes (`/guild/<id>`) now require proper access

## Security Features

1. **Guild Access Control**: Users can only access data from Discord servers they're actually members of
2. **Bot Presence Verification**: Only servers where your bot is installed are accessible
3. **Session Management**: User authentication is maintained via Flask sessions
4. **Secure Redirects**: Unauthorized users are redirected to login or subscription pages

## Testing

1. Visit `http://127.0.0.1:25594/` - should show subscription page with login button
2. Click "Login with Discord" - redirects to Discord OAuth
3. After authentication, behavior depends on guild membership:
   - If user is in servers with the bot: redirect to dashboard
   - If user has no accessible servers: show subscription page with username

## Production Deployment

For production deployment:
1. Update `DISCORD_REDIRECT_URI` in `.env` to use your production domain
2. Add the production redirect URI in your Discord application OAuth settings
3. Ensure your `SECRET_KEY` is secure and random
4. Consider using HTTPS for OAuth callbacks

## Database Schema

The system relies on the `guild_settings` table to determine which guilds have the bot:
- `guild_id`: Discord server ID
- `is_active`: Whether the bot is active in this server
- `guild_name`: Display name for the server

Make sure this table is populated with your bot's installed servers.
