

# Quick Performance Fix for Discord OAuth
import aiohttp
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

# Global session for Discord API (connection pooling)
_discord_session = None

def get_discord_session():
    """Get reusable Discord session with connection pooling."""
    global _discord_session
    if _discord_session is None or _discord_session.closed:
        connector = aiohttp.TCPConnector(
            limit=50,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30
        )
        timeout = aiohttp.ClientTimeout(total=8, connect=3)
        _discord_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'DBSBM-Bot/1.0'}
        )
    return _discord_session

async def fast_discord_auth(code):
    """Fast Discord authentication with concurrent API calls."""
    try:
        session = get_discord_session()
        
        # Step 1: Exchange code for token
        token_data = {
            'client_id': os.getenv('DISCORD_CLIENT_ID'),
            'client_secret': os.getenv('DISCORD_CLIENT_SECRET'),
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': os.getenv('DISCORD_REDIRECT_URI')
        }
        
        async with session.post('https://discord.com/api/oauth2/token', data=token_data) as response:
            if response.status != 200:
                return None, None, []
            token_response = await response.json()
        
        access_token = token_response.get('access_token')
        if not access_token:
            return None, None, []
        
        # Step 2: Get user info and guilds concurrently
        headers = {'Authorization': f'Bearer {access_token}'}
        
        user_task = session.get('https://discord.com/api/users/@me', headers=headers)
        guilds_task = session.get('https://discord.com/api/users/@me/guilds', headers=headers)
        
        async with user_task as user_resp, guilds_task as guilds_resp:
            if user_resp.status != 200:
                return None, None, []
            
            user_info = await user_resp.json()
            user_guilds = []
            
            if guilds_resp.status == 200:
                user_guilds = await guilds_resp.json()
        
        return token_response, user_info, user_guilds
        
    except Exception as e:
        logger.error(f"Fast Discord auth error: {e}")
        return None, None, []

def discord_callback_fast():
    """Fast Discord OAuth callback (replaces slow version)."""
    start_time = time.time()
    
    code = request.args.get('code')
    if not code:
        return redirect(url_for('index'))
    
    # Run async Discord auth
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        token_data, user_info, user_guilds = loop.run_until_complete(fast_discord_auth(code))
    finally:
        loop.close()
    
    if not user_info:
        return redirect(url_for('index'))
    
    # Get accessible guilds (with simple caching)
    accessible_guilds = get_user_accessible_guilds(user_guilds)
    
    # Store in session
    session['discord_user'] = {
        'id': user_info['id'],
        'username': user_info['username'],
        'discriminator': user_info.get('discriminator', '0000'),
        'avatar': user_info.get('avatar'),
        'accessible_guilds': accessible_guilds,
        'auth_time': time.time()
    }
    
    auth_time = time.time() - start_time
    logger.info(f"🚀 Fast Discord auth completed in {auth_time:.2f}s")
    
    # Redirect
    if accessible_guilds:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('subscribe'))

# Replace the slow callback function
app.add_url_rule('/auth/discord/callback', 'discord_callback_fast', discord_callback_fast, methods=['GET'])
