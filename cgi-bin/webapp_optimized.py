import os
import logging
import logging.handlers
import sys
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import psycopg2
from psycopg2 import OperationalError
import json
import requests
from dotenv import load_dotenv
import redis
import hashlib

# Load environment variables from .env file
load_dotenv()


class DailyRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """Handler that creates a new log file each day."""

    def __init__(self, filename: str, when: str = "midnight", interval: int = 1, backup_count: int = 30):
        # Ensure the directory exists
        log_dir = os.path.dirname(filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        super().__init__(filename, when=when, interval=interval, backupCount=backup_count)
        self.suffix = "%Y-%m-%d"
        self.namer = self._namer

    def _namer(self, default_name: str) -> str:
        """Custom namer to use date format in filename."""
        base_name = os.path.splitext(default_name)[0]
        extension = os.path.splitext(default_name)[1]
        return f"{base_name}{extension}"


# Configure logging to use daily files
handlers = [
    # Daily rotating file handler
    DailyRotatingFileHandler(
        'db_logs/webapp_daily.log',
        when="midnight",
        interval=1,
        backup_count=30
    )
]

# Add console handler only if debug mode is enabled
if os.getenv('FLASK_DEBUG', '0').lower() == 'true':
    handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder="../../StaticFiles/DBSBM/static", template_folder="bot/templates")

# Configure for production
app.config['ENV'] = os.getenv('FLASK_ENV', 'production')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', '0').lower() == 'true'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

# Handle proxy headers (useful for hosting platforms)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Redis Configuration
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        username=os.getenv('REDIS_USERNAME', None),
        password=os.getenv('REDIS_PASSWORD', None),
        db=int(os.getenv('REDIS_DB', 0)),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )
    # Test connection
    redis_client.ping()
    logger.info("[OK] Redis connection established successfully")
except Exception as e:
    logger.error(f"[ERROR] Redis connection failed: {e}")
    redis_client = None

def get_cache_key(*args):
    """Generate a cache key from arguments."""
    key_string = "|".join(str(arg) for arg in args)
    return hashlib.md5(key_string.encode()).hexdigest()

def cache_get(key, default=None):
    """Get value from Redis cache."""
    if not redis_client:
        return default
    try:
        value = redis_client.get(key)
        return json.loads(value) if value else default
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return default

def cache_set(key, value, expire=300):
    """Set value in Redis cache with expiration (default 5 minutes)."""
    if not redis_client:
        return False
    try:
        redis_client.setex(key, expire, json.dumps(value))
        return True
    except Exception as e:
        logger.error(f"Cache set error: {e}")
        return False

def get_db_connection():
    """Create database connection with optimized settings."""
    try:
        # Try PostgreSQL first (preferred)
        if os.getenv('POSTGRES_HOST'):
            connection = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', ''),
                database=os.getenv('POSTGRES_DB', 'dbsbm'),
                port=int(os.getenv('POSTGRES_PORT', 5432))
            )
            connection.autocommit = True
            return connection
        else:
            # Fallback to MySQL
            connection = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST', 'localhost'),
                user=os.getenv('MYSQL_USER', 'dbsbm'),
                password=os.getenv('MYSQL_PASSWORD', ''),
                database=os.getenv('MYSQL_DB', 'dbsbm'),
                port=int(os.getenv('MYSQL_PORT', 3306)),
                # Performance optimizations
                connection_timeout=5,
                autocommit=True,
                pool_name='web_pool',
                pool_size=10,
                pool_reset_session=True
            )
            return connection
    except (OperationalError, Error) as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def get_active_guilds():
    """Get active guilds with their stats."""
    # Check cache first
    cache_key = get_cache_key("active_guilds")
    cached_result = cache_get(cache_key)
    if cached_result is not None:
        return cached_result
    
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get guilds from guild_settings with their real names and monthly/yearly units
        query = """
        SELECT 
            gs.guild_id,
            COALESCE(gs.guild_name, CONCAT('Guild ', RIGHT(gs.guild_id, 6))) as guild_name,
            gs.subscription_level,
            COALESCE(SUM(CASE 
                WHEN b.created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH) 
                THEN b.units 
                ELSE 0 
            END), 0) as monthly_units,
            COALESCE(SUM(CASE 
                WHEN b.created_at >= DATE_SUB(NOW(), INTERVAL 1 YEAR) 
                THEN b.units 
                ELSE 0 
            END), 0) as yearly_units
        FROM guild_settings gs
        LEFT JOIN bets b ON gs.guild_id = b.guild_id
        WHERE gs.is_active = 1
        GROUP BY gs.guild_id, gs.guild_name, gs.subscription_level
        ORDER BY yearly_units DESC
        LIMIT 10
        """
        
        cursor.execute(query)
        guilds = cursor.fetchall()
        cursor.close()
        
        # Cache for 2 minutes
        cache_set(cache_key, guilds, expire=120)
        return guilds
        
    except Error as e:
        logger.error(f"Error fetching active guilds: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()


def get_guild_customization(guild_id):
    """Get guild customization settings."""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM guild_customization 
                WHERE guild_id = %s
            """, (guild_id,))
            customization = cursor.fetchone()
            cursor.close()
            connection.close()
            
            # Return default settings if none exist
            if not customization:
                return {
                    'guild_id': guild_id,
                    'page_title': None,
                    'page_description': None,
                    'welcome_message': None,
                    'primary_color': '#667eea',
                    'secondary_color': '#764ba2',
                    'accent_color': '#5865F2',
                    'hero_image': None,
                    'logo_image': None,
                    'background_image': None,
                    'about_section': None,
                    'features_section': None,
                    'rules_section': None,
                    'discord_invite': None,
                    'website_url': None,
                    'twitter_url': None,
                    'show_leaderboard': True,
                    'show_recent_bets': True,
                    'show_stats': True,
                    'public_access': False
                }
            return customization
    except Error as e:
        logger.error(f"Error fetching guild customization: {e}")
        return None


def create_default_guild_customization(guild_id, guild_name=None):
    """Create default customization settings for a new guild."""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Check if customization already exists
            cursor.execute("SELECT id FROM guild_customization WHERE guild_id = %s", (guild_id,))
            if cursor.fetchone():
                cursor.close()
                connection.close()
                return True
                
            # Create default customization
            default_title = f"{guild_name} Betting Hub" if guild_name else f"Guild {str(guild_id)[-6:]} Betting Hub"
            default_description = "Track bets, compete with friends, and analyze your betting performance."
            default_welcome = f"Welcome to {guild_name or 'our betting community'}! Track your bets and see how you stack up against other members."
            
            cursor.execute("""
                INSERT INTO guild_customization (
                    guild_id, page_title, page_description, welcome_message,
                    primary_color, secondary_color, accent_color,
                    show_leaderboard, show_recent_bets, show_stats, public_access
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                guild_id, default_title, default_description, default_welcome,
                '#667eea', '#764ba2', '#5865F2',
                True, True, True, False
            ))
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        logger.error(f"Error creating default guild customization: {e}")
        return False


def update_guild_customization(guild_id, settings):
    """Update guild customization settings."""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Build dynamic update query
            set_clauses = []
            values = []
            
            allowed_fields = [
                'page_title', 'page_description', 'welcome_message',
                'primary_color', 'secondary_color', 'accent_color',
                'hero_image', 'logo_image', 'background_image',
                'about_section', 'features_section', 'rules_section',
                'discord_invite', 'website_url', 'twitter_url',
                'show_leaderboard', 'show_recent_bets', 'show_stats', 'public_access'
            ]
            
            for field in allowed_fields:
                if field in settings:
                    set_clauses.append(f"{field} = %s")
                    values.append(settings[field])
            
            if not set_clauses:
                return False
                
            values.append(guild_id)
            query = f"""
                INSERT INTO guild_customization (guild_id, {', '.join(allowed_fields)})
                VALUES (%s, {', '.join(['%s'] * len(allowed_fields))})
                ON DUPLICATE KEY UPDATE {', '.join(set_clauses)}
            """
            
            # For INSERT part, we need all values
            insert_values = [guild_id] + [settings.get(field) for field in allowed_fields]
            
            cursor.execute(f"""
                INSERT INTO guild_customization (guild_id, {', '.join(allowed_fields)})
                VALUES ({', '.join(['%s'] * (len(allowed_fields) + 1))})
                ON DUPLICATE KEY UPDATE {', '.join(set_clauses)}
            """, insert_values + values)
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        logger.error(f"Error updating guild customization: {e}")
        return False


def check_guild_admin_access(guild_id):
    """Check if current user has admin access to guild."""
    if 'discord_user' not in session:
        return False
    
    user_guilds = session['discord_user'].get('accessible_guilds', [])
    for guild in user_guilds:
        if guild['id'] == str(guild_id):
            # Check if user has admin permissions (manage server, administrator, etc.)
            permissions = guild.get('permissions', 0)
            # 0x8 = Administrator, 0x20 = Manage Guild
            return (permissions & 0x8) == 0x8 or (permissions & 0x20) == 0x20
    return False


def get_guild_public_stats(guild_id):
    """Get public guild statistics."""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT user_id) as total_bettors,
                    COUNT(*) as total_bets,
                    COALESCE(SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END), 0) as total_wins,
                    COALESCE(SUM(CASE WHEN result = 'lost' THEN 1 ELSE 0 END), 0) as total_losses,
                    COALESCE(SUM(CASE WHEN result = 'won' THEN profit_loss ELSE 0 END), 0) as total_winnings,
                    COALESCE(SUM(profit_loss), 0) as net_profit
                FROM bets 
                WHERE guild_id = %s AND result IN ('won', 'lost')
            """, (guild_id,))
            stats = cursor.fetchone()
            cursor.close()
            connection.close()
            return stats
    except Error as e:
        logger.error(f"Error fetching guild public stats: {e}")
        return None


def get_guild_leaderboard(guild_id, limit=10):
    """Get guild leaderboard."""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    user_id,
                    COUNT(*) as total_bets,
                    SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN result = 'lost' THEN 1 ELSE 0 END) as losses,
                    ROUND(
                        (SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) * 100.0) / 
                        NULLIF(SUM(CASE WHEN result IN ('won', 'lost') THEN 1 ELSE 0 END), 0), 
                        1
                    ) as win_rate,
                    COALESCE(SUM(profit_loss), 0) as net_profit
                FROM bets 
                WHERE guild_id = %s AND result IN ('won', 'lost')
                GROUP BY user_id
                HAVING total_bets >= 3
                ORDER BY net_profit DESC, win_rate DESC
                LIMIT %s
            """, (guild_id, limit))
            leaderboard = cursor.fetchall()
            cursor.close()
            connection.close()
            return leaderboard
    except Error as e:
        logger.error(f"Error fetching guild leaderboard: {e}")
        return []



def get_live_games():
    """Get live games from database."""
    # Check cache first (cache for 30 seconds since live data changes frequently)
    cache_key = get_cache_key("live_games")
    cached_result = cache_get(cache_key)
    if cached_result is not None:
        return cached_result
    
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get live games - simplified query based on actual schema
        query = """
        SELECT 
            g.id as game_id,
            g.api_game_id,
            g.league_id,
            g.league_name,
            g.home_team_id,
            g.away_team_id,
            g.home_team_name,
            g.away_team_name,
            g.home_team_logo,
            g.away_team_logo,
            g.start_time,
            g.status,
            g.score
        FROM games g
        WHERE g.status IN ('live', 'halftime', 'scheduled', 'finished')
        AND g.start_time >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        ORDER BY g.start_time ASC
        LIMIT 50
        """
        
        cursor.execute(query)
        games = cursor.fetchall()
        
        # Group games by league
        leagues = {}
        for game in games:
            league_id = game['league_id']
            league_name = game['league_name'] or f"League {league_id}"
            
            if league_id not in leagues:
                leagues[league_id] = {
                    'id': league_id,
                    'name': league_name,
                    'logo': None,  # No league logo in current schema
                    'games': []
                }
            
            # Parse score if it exists
            score_data = None
            if game['score']:
                try:
                    import json
                    score_info = json.loads(game['score'])
                    if isinstance(score_info, dict):
                        score_data = {
                            'home': score_info.get('home', 0),
                            'away': score_info.get('away', 0)
                        }
                except:
                    score_data = None
            
            # Format game data
            game_data = {
                'game_id': game['game_id'],
                'home_team_name': game['home_team_name'],
                'home_logo': game['home_team_logo'],
                'away_team_name': game['away_team_name'],
                'away_logo': game['away_team_logo'],
                'start_time': game['start_time'],
                'status': game['status'],
                'score': score_data
            }
            
            leagues[league_id]['games'].append(game_data)
        
        cursor.close()
        result = list(leagues.values())
        
        # Cache for 30 seconds (live data)
        cache_set(cache_key, result, expire=30)
        return result
        
    except Error as e:
        logger.error(f"Error fetching live games: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()

def get_guild_stats(guild_id):
    """Get guild statistics for today."""
    # Check cache first (cache for 60 seconds)
    cache_key = get_cache_key("guild_stats", guild_id)
    cached_result = cache_get(cache_key)
    if cached_result is not None:
        return cached_result
    
    try:
        connection = get_db_connection()
        if not connection:
            return {}
        
        cursor = connection.cursor(dictionary=True)
        
        # Get today's bets count - handle different possible column names
        try:
            cursor.execute("""
                SELECT COUNT(*) as today_bets
                FROM bets 
                WHERE guild_id = %s 
                AND DATE(created_at) = CURDATE()
            """, (guild_id,))
            today_bets = cursor.fetchone()['today_bets']
        except Exception as e:
            logger.warning(f"Error getting today's bets: {e}")
            today_bets = 0
        
        # Get today's units - handle different status values
        try:
            cursor.execute("""
                SELECT COALESCE(SUM(units), 0) as today_units
                FROM bets 
                WHERE guild_id = %s 
                AND DATE(created_at) = CURDATE()
                AND status IN ('won', 'lost', 'WON', 'LOST')
            """, (guild_id,))
            today_units = cursor.fetchone()['today_units']
        except Exception as e:
            logger.warning(f"Error getting today's units: {e}")
            today_units = 0
        
        # Get active users (users who placed bets today)
        try:
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) as active_users
                FROM bets 
                WHERE guild_id = %s 
                AND DATE(created_at) = CURDATE()
            """, (guild_id,))
            active_users = cursor.fetchone()['active_users']
        except Exception as e:
            logger.warning(f"Error getting active users: {e}")
            active_users = 0
        
        # Get win rate (last 30 days) - handle different status values
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_bets,
                    SUM(CASE WHEN status IN ('won', 'WON') THEN 1 ELSE 0 END) as won_bets
                FROM bets 
                WHERE guild_id = %s 
                AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                AND status IN ('won', 'lost', 'WON', 'LOST')
            """, (guild_id,))
            win_stats = cursor.fetchone()
            
            win_rate = 0
            if win_stats['total_bets'] > 0:
                win_rate = (win_stats['won_bets'] / win_stats['total_bets']) * 100
        except Exception as e:
            logger.warning(f"Error getting win rate: {e}")
            win_rate = 0
        
        cursor.close()
        connection.close()
        
        result = {
            'today_bets': today_bets,
            'today_units': today_units,
            'active_users': active_users,
            'win_rate': win_rate
        }
        
        # Cache for 60 seconds
        cache_set(cache_key, result, expire=60)
        return result
        
    except Exception as e:
        logger.error(f"Error getting guild stats: {e}")
        return {
            'today_bets': 0,
            'today_units': 0,
            'active_users': 0,
            'win_rate': 0
        }

def get_recent_activity(guild_id, limit=10):
    """Get recent activity for the guild."""
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # Get recent bets and their outcomes - handle different column names
        try:
            cursor.execute("""
                SELECT 
                    b.bet_serial,
                    b.user_id,
                    b.bet_type,
                    b.units,
                    b.status,
                    b.created_at,
                    b.updated_at,
                    COALESCE(u.username, u.display_name, 'Unknown User') as username
                FROM bets b
                LEFT JOIN users u ON b.user_id = u.user_id
                WHERE b.guild_id = %s
                ORDER BY b.created_at DESC
                LIMIT %s
            """, (guild_id, limit))
        except Exception as e:
            # Fallback query if username column doesn't exist
            logger.warning(f"Error with username join: {e}")
            cursor.execute("""
                SELECT 
                    bet_serial,
                    user_id,
                    bet_type,
                    units,
                    status,
                    created_at,
                    updated_at
                FROM bets 
                WHERE guild_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (guild_id, limit))
        
        bets = cursor.fetchall()
        activity = []
        
        for bet in bets:
            username = bet.get('username', f'User {bet["user_id"]}')
            bet_type = bet.get('bet_type', 'bet')
            units = bet.get('units', 0)
            status = bet.get('status', 'pending')
            
            if status in ['won', 'WON']:
                icon = 'trophy'
                message = f"{username} won {units} units on {bet_type}"
            elif status in ['lost', 'LOST']:
                icon = 'times-circle'
                message = f"{username} lost {units} units on {bet_type}"
            else:
                icon = 'clock'
                message = f"{username} placed a {bet_type} bet for {units} units"
            
            timestamp = 'Unknown'
            if bet.get('created_at'):
                try:
                    timestamp = bet['created_at'].strftime('%I:%M %p')
                except:
                    timestamp = 'Unknown'
            
            activity.append({
                'icon': icon,
                'message': message,
                'timestamp': timestamp
            })
        
        cursor.close()
        connection.close()
        
        return activity
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return []

# Discord OAuth Helper Functions
def get_discord_oauth_url():
    """Generate Discord OAuth URL for user authentication."""
    client_id = os.getenv('DISCORD_CLIENT_ID')
    redirect_uri = os.getenv('DISCORD_REDIRECT_URI')
    scope = 'identify guilds'
    
    oauth_url = (
        f"https://discord.com/api/oauth2/authorize?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scope}"
    )
    return oauth_url

def exchange_discord_code(code):
    """Exchange Discord OAuth code for access token."""
    try:
        data = {
            'client_id': os.getenv('DISCORD_CLIENT_ID'),
            'client_secret': os.getenv('DISCORD_CLIENT_SECRET'),
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': os.getenv('DISCORD_REDIRECT_URI')
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
        return response.json() if response.status_code == 200 else None
        
    except Exception as e:
        logger.error(f"Error exchanging Discord code: {e}")
        return None

def get_discord_user_info(access_token):
    """Get Discord user information using access token."""
    try:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get('https://discord.com/api/users/@me', headers=headers)
        return response.json() if response.status_code == 200 else None
        
    except Exception as e:
        logger.error(f"Error getting Discord user info: {e}")
        return None

def get_discord_user_guilds(access_token):
    """Get Discord guilds the user is a member of."""
    try:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get('https://discord.com/api/users/@me/guilds', headers=headers)
        return response.json() if response.status_code == 200 else []
        
    except Exception as e:
        logger.error(f"Error getting Discord user guilds: {e}")
        return []

def get_bot_guilds():
    """Get guilds where the bot is present."""
    try:
        # This would require the bot to be running and accessible
        # For now, we'll check against the database
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT guild_id FROM guild_settings WHERE is_active = 1")
        bot_guilds = [str(row['guild_id']) for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        
        return bot_guilds
        
    except Exception as e:
        logger.error(f"Error getting bot guilds: {e}")
        return []

def get_user_accessible_guilds(user_guilds):
    """Get guilds where user is a member AND bot is present."""
    try:
        bot_guilds = get_bot_guilds()
        user_guild_ids = [guild['id'] for guild in user_guilds]
        
        # Find intersection of user guilds and bot guilds
        accessible_guilds = []
        for guild in user_guilds:
            if guild['id'] in bot_guilds:
                accessible_guilds.append(guild)
        
        return accessible_guilds
        
    except Exception as e:
        logger.error(f"Error getting user accessible guilds: {e}")
        return []

def get_user_guild_roles(guild_id, user_id, access_token):
    """Get user's roles in a specific Discord guild."""
    try:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # Get guild member info to see their roles
        response = requests.get(f'https://discord.com/api/guilds/{guild_id}/members/{user_id}', headers=headers)
        if response.status_code == 200:
            member_data = response.json()
            return member_data.get('roles', [])
        else:
            logger.warning(f"Could not get user roles for guild {guild_id}: {response.status_code}")
            return []
        
    except Exception as e:
        logger.error(f"Error getting user guild roles: {e}")
        return []

def check_user_role_access(guild_id, required_role_type='member'):
    """Check if user has required role access in guild."""
    try:
        discord_user = session.get('discord_user')
        if not discord_user:
            return False
        
        # Get guild settings to find admin role
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("""
            SELECT admin_role, command_channel_1
            FROM guild_settings 
            WHERE guild_id = %s
        """, (guild_id,))
        
        guild_settings = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if not guild_settings:
            return False
        
        admin_role = guild_settings[0]
        
        # Get user's guild info from session
        accessible_guilds = discord_user.get('accessible_guilds', [])
        user_guild = None
        
        for guild in accessible_guilds:
            if guild['id'] == str(guild_id):
                user_guild = guild
                break
        
        if not user_guild:
            return False
        
        # Check permissions - if they have admin permissions, they can access admin pages
        permissions = user_guild.get('permissions', 0)
        
        if required_role_type == 'admin':
            # Check if user has administrator or manage guild permissions
            has_admin_perms = (permissions & 0x8) == 0x8 or (permissions & 0x20) == 0x20
            return has_admin_perms
        
        elif required_role_type == 'member':
            # Any guild member can access member pages
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking user role access: {e}")
        return False

def get_user_access_level(guild_id):
    """Determine user's access level in guild (admin, member, or none)."""
    try:
        discord_user = session.get('discord_user')
        if not discord_user:
            return 'none'
        
        # Check if user has access to guild at all
        if not check_guild_access(guild_id):
            return 'none'
        
        # Check if user has admin access
        if check_user_role_access(guild_id, 'admin'):
            return 'admin'
        
        # Check if user has member access
        if check_user_role_access(guild_id, 'member'):
            return 'member'
        
        return 'none'
        
    except Exception as e:
        logger.error(f"Error determining user access level: {e}")
        return 'none'

def check_guild_access(guild_id):
    """Check if the current user has access to a specific guild."""
    discord_user = session.get('discord_user')
    if not discord_user:
        return False
    
    accessible_guilds = discord_user.get('accessible_guilds', [])
    return str(guild_id) in [guild['id'] for guild in accessible_guilds]

def require_guild_access(guild_id):
    """Decorator to require guild access for a route."""
    def decorator(f):
        def wrapper(*args, **kwargs):
            if not check_guild_access(guild_id):
                return redirect(url_for('discord_login'))
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

@app.route('/dashboard')
@app.route('/guild-dashboard')
def dashboard():
    """Guild Dashboard - Lists all guilds the user has access to"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all guilds with their settings and stats
        query = """
        SELECT 
            g.guild_id,
            g.guild_name,
            gs.embed_channel_1,
            gs.command_channel_1,
            gs.admin_role,
            gs.base_unit_value,
            gs.premium_enabled,
            COUNT(DISTINCT b.bet_id) as total_bets,
            COUNT(DISTINCT u.user_id) as total_users
        FROM guilds g
        LEFT JOIN guild_settings gs ON g.guild_id = gs.guild_id
        LEFT JOIN bets b ON g.guild_id = b.guild_id
        LEFT JOIN users u ON g.guild_id = u.guild_id
        GROUP BY g.guild_id, g.guild_name, gs.embed_channel_1, gs.command_channel_1, 
                 gs.admin_role, gs.base_unit_value, gs.premium_enabled
        ORDER BY g.guild_name
        """
        
        cursor.execute(query)
        guilds = cursor.fetchall()
        
        # Convert to list of dictionaries for easier template handling
        guild_list = []
        for guild in guilds:
            guild_dict = {
                'guild_id': guild[0],
                'guild_name': guild[1],
                'embed_channel': guild[2],
                'command_channel': guild[3],
                'admin_role': guild[4],
                'base_unit_value': guild[5] or 1.0,
                'premium_enabled': guild[6] or False,
                'total_bets': guild[7] or 0,
                'total_users': guild[8] or 0
            }
            guild_list.append(guild_dict)
        
        cursor.close()
        conn.close()
        
        # Get Discord client ID from environment for invite links
        discord_client_id = os.getenv('DISCORD_CLIENT_ID', '1341993312915034153')
        
        return render_template('guild_dashboard.html', 
                             guilds=guild_list,
                             discord_client_id=discord_client_id)
        
    except Exception as e:
        logger.error(f"Error in guild_dashboard: {e}")
        return render_template('error.html', error="Unable to load guild dashboard")

@app.route('/')
def index():
    """Main landing page - shows subscription page if no active guilds, otherwise dashboard."""
    try:
        # Check if user is authenticated with Discord
        discord_user = session.get('discord_user')
        
        if discord_user:
            # User is authenticated - check their accessible guilds
            accessible_guilds = discord_user.get('accessible_guilds', [])
            
            if accessible_guilds:
                # User has access to guilds with the bot - show dashboard
                leagues = get_live_games()
                active_guilds = get_active_guilds()
                return render_template('landing.html', 
                                    leagues=leagues, 
                                    active_guilds=active_guilds,
                                    discord_user=discord_user)
            else:
                # User authenticated but no access to guilds with bot
                return render_template('subscription_landing.html', 
                                    discord_user=discord_user)
        else:
            # User not authenticated - show subscription page with login option
            return render_template('subscription_landing.html')
            
    except Exception as e:
        logger.error(f"Error rendering landing page: {e}")
        # On error, default to subscription page to encourage setup
        return render_template('subscription_landing.html')

@app.route('/server-list')
def server_list():
    """Server list page."""
    try:
        active_guilds = get_active_guilds()
        return render_template('server_list.html', guilds=active_guilds)
    except Exception as e:
        logger.error(f"Error rendering server list: {e}")
        return render_template('server_list.html', guilds=[])

@app.route('/subscribe')
def subscribe():
    """Subscription landing page."""
    return render_template('subscription_landing.html')

@app.route('/premium')
def premium():
    """Premium subscription page."""
    return render_template('premium.html')

@app.route('/platinum')
def platinum():
    """Platinum subscription page."""
    return render_template('platinum.html')

# Discord OAuth Routes
@app.route('/auth/discord')
def discord_login():
    """Redirect to Discord OAuth."""
    return redirect(get_discord_oauth_url())

@app.route('/auth/discord/callback')
def discord_callback():
    """Handle Discord OAuth callback."""
    code = request.args.get('code')
    if not code:
        return redirect(url_for('index'))
    
    # Exchange code for access token
    token_data = exchange_discord_code(code)
    if not token_data or 'access_token' not in token_data:
        return redirect(url_for('index'))
    
    access_token = token_data['access_token']
    
    # Get user info
    user_info = get_discord_user_info(access_token)
    if not user_info:
        return redirect(url_for('index'))
    
    # Get user guilds
    user_guilds = get_discord_user_guilds(access_token)
    
    # Get accessible guilds (where user is member AND bot is present)
    accessible_guilds = get_user_accessible_guilds(user_guilds)
    
    # Store user info in session
    session['discord_user'] = {
        'id': user_info['id'],
        'username': user_info['username'],
        'discriminator': user_info.get('discriminator', '0000'),
        'avatar': user_info.get('avatar'),
        'accessible_guilds': accessible_guilds
    }
    
    # Redirect based on accessible guilds
    if accessible_guilds:
        # User has access to at least one guild with the bot
        return redirect(url_for('dashboard'))
    else:
        # User has no access to guilds with the bot
        return redirect(url_for('subscribe'))

@app.route('/auth/logout')
def logout():
    """Logout user by clearing session."""
    session.clear()
    return redirect(url_for('index'))

@app.route('/guild/<int:guild_id>')
def guild_home(guild_id):
    """Guild home page - redirects based on user role."""
    try:
        # Check if user has access to this guild
        if not check_guild_access(guild_id):
            return redirect(url_for('discord_login'))
        
        # Determine user's access level
        access_level = get_user_access_level(guild_id)
        
        if access_level == 'admin':
            # Redirect to admin page
            return redirect(url_for('guild_admin_page', guild_id=guild_id))
        elif access_level == 'member':
            # Redirect to member page
            return redirect(url_for('guild_member_page', guild_id=guild_id))
        else:
            # No appropriate access
            return redirect(url_for('discord_login'))
        
    except Exception as e:
        logger.error(f"Error in guild_home: {e}")
        return redirect(url_for('index'))

@app.route('/guild/<int:guild_id>/admin')
def guild_admin_page(guild_id):
    """Guild admin page with full management capabilities."""
    try:
        # Check admin access
        if not check_user_role_access(guild_id, 'admin'):
            return redirect(url_for('guild_member_page', guild_id=guild_id))
        
        # Get guild info
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT 
                    g.guild_id,
                    g.guild_name,
                    gs.embed_channel_1,
                    gs.command_channel_1,
                    gs.admin_role,
                    gs.base_unit_value,
                    gs.premium_enabled,
                    gs.subscription_level
                FROM guilds g
                LEFT JOIN guild_settings gs ON g.guild_id = gs.guild_id
                WHERE g.guild_id = %s
            """, (guild_id,))
            guild = cursor.fetchone()
            
            if guild:
                # Get comprehensive admin statistics
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT b.user_id) as total_users,
                        COUNT(b.bet_id) as total_bets,
                        SUM(CASE WHEN b.bet_won = 1 THEN 1 ELSE 0 END) as total_wins,
                        SUM(CASE WHEN b.bet_loss = 1 THEN 1 ELSE 0 END) as total_losses,
                        AVG(b.bet_amount) as avg_bet_amount,
                        SUM(b.bet_amount) as total_volume
                    FROM bets b
                    WHERE b.guild_id = %s
                """, (guild_id,))
                admin_stats = cursor.fetchone()
                
                # Get recent user activity
                cursor.execute("""
                    SELECT 
                        b.user_id,
                        b.bet_amount,
                        b.odds,
                        b.bet_description,
                        b.created_at,
                        b.bet_won,
                        b.bet_loss
                    FROM bets b
                    WHERE b.guild_id = %s
                    ORDER BY b.created_at DESC
                    LIMIT 20
                """, (guild_id,))
                recent_activity = cursor.fetchall()
                
                cursor.close()
                connection.close()
                
                guild_data = {
                    'guild_id': guild[0],
                    'guild_name': guild[1],
                    'embed_channel': guild[2],
                    'command_channel': guild[3],
                    'admin_role': guild[4],
                    'base_unit_value': guild[5] or 1.0,
                    'premium_enabled': guild[6] or False,
                    'subscription_level': guild[7] or 'free'
                }
                
                stats_data = {
                    'total_users': admin_stats[0] or 0,
                    'total_bets': admin_stats[1] or 0,
                    'total_wins': admin_stats[2] or 0,
                    'total_losses': admin_stats[3] or 0,
                    'avg_bet_amount': admin_stats[4] or 0,
                    'total_volume': admin_stats[5] or 0
                }
                
                return render_template('guild_admin.html', 
                                     guild=guild_data,
                                     stats=stats_data,
                                     recent_activity=recent_activity,
                                     guild_id=guild_id)
        
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error rendering guild admin page: {e}")
        return redirect(url_for('index'))

@app.route('/guild/<int:guild_id>/member')
def guild_member_page(guild_id):
    """Guild member page with limited access."""
    try:
        # Check member access
        if not check_user_role_access(guild_id, 'member'):
            return redirect(url_for('discord_login'))
        
        # Get guild info
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT 
                    g.guild_id,
                    g.guild_name,
                    gs.base_unit_value,
                    gs.premium_enabled
                FROM guilds g
                LEFT JOIN guild_settings gs ON g.guild_id = gs.guild_id
                WHERE g.guild_id = %s
            """, (guild_id,))
            guild = cursor.fetchone()
            
            if guild:
                # Get user's personal stats
                user_id = session.get('discord_user', {}).get('id')
                cursor.execute("""
                    SELECT 
                        COUNT(b.bet_id) as my_total_bets,
                        SUM(CASE WHEN b.bet_won = 1 THEN 1 ELSE 0 END) as my_wins,
                        SUM(CASE WHEN b.bet_loss = 1 THEN 1 ELSE 0 END) as my_losses,
                        AVG(b.bet_amount) as my_avg_bet,
                        SUM(b.bet_amount) as my_total_wagered
                    FROM bets b
                    WHERE b.guild_id = %s AND b.user_id = %s
                """, (guild_id, user_id))
                user_stats = cursor.fetchone()
                
                # Get guild leaderboard (top 10)
                cursor.execute("""
                    SELECT 
                        b.user_id,
                        COUNT(b.bet_id) as total_bets,
                        SUM(CASE WHEN b.bet_won = 1 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN b.bet_loss = 1 THEN 1 ELSE 0 END) as losses,
                        SUM(b.bet_amount) as total_wagered
                    FROM bets b
                    WHERE b.guild_id = %s
                    GROUP BY b.user_id
                    ORDER BY wins DESC, total_bets DESC
                    LIMIT 10
                """, (guild_id,))
                leaderboard = cursor.fetchall()
                
                # Get user's recent bets
                cursor.execute("""
                    SELECT 
                        b.bet_amount,
                        b.odds,
                        b.bet_description,
                        b.created_at,
                        b.bet_won,
                        b.bet_loss
                    FROM bets b
                    WHERE b.guild_id = %s AND b.user_id = %s
                    ORDER BY b.created_at DESC
                    LIMIT 10
                """, (guild_id, user_id))
                my_recent_bets = cursor.fetchall()
                
                cursor.close()
                connection.close()
                
                guild_data = {
                    'guild_id': guild[0],
                    'guild_name': guild[1],
                    'base_unit_value': guild[2] or 1.0,
                    'premium_enabled': guild[3] or False
                }
                
                user_stats_data = {
                    'total_bets': user_stats[0] or 0,
                    'wins': user_stats[1] or 0,
                    'losses': user_stats[2] or 0,
                    'avg_bet': user_stats[3] or 0,
                    'total_wagered': user_stats[4] or 0
                }
                
                return render_template('guild_member.html', 
                                     guild=guild_data,
                                     user_stats=user_stats_data,
                                     leaderboard=leaderboard,
                                     my_recent_bets=my_recent_bets,
                                     guild_id=guild_id)
        
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error rendering guild member page: {e}")
        return redirect(url_for('index'))

@app.route('/guild/<int:guild_id>/live-scores')
def live_scores(guild_id):
    """Live scores page for a specific guild."""
    try:
        leagues = get_live_games()
        return render_template('live_scores.html', 
                            guild_id=guild_id, 
                            leagues=leagues)
    except Exception as e:
        logger.error(f"Error rendering live scores: {e}")
        return render_template('live_scores.html', 
                            guild_id=guild_id, 
                            leagues=[])

@app.route('/guild/<int:guild_id>/player-stats')
def player_stats(guild_id):
    """Player stats page."""
    try:
        return render_template('player_stats.html', guild_id=guild_id)
    except Exception as e:
        logger.error(f"Error rendering player stats: {e}")
        return render_template('player_stats.html', guild_id=guild_id)

@app.route('/guild/<int:guild_id>/odds-buster')
def odds_buster(guild_id):
    """Odds buster page."""
    try:
        return render_template('odds_buster.html', guild_id=guild_id)
    except Exception as e:
        logger.error(f"Error rendering odds buster: {e}")
        return render_template('odds_buster.html', guild_id=guild_id)

@app.route('/guild/<int:guild_id>/playmaker-stats')
def playmaker_stats(guild_id):
    """Playmaker stats page."""
    try:
        return render_template('playmaker_stats.html', guild_id=guild_id)
    except Exception as e:
        logger.error(f"Error rendering playmaker stats: {e}")
        return render_template('playmaker_stats.html', guild_id=guild_id)

@app.route('/guild/<int:guild_id>/settings')
def guild_settings(guild_id):
    """Guild settings page."""
    try:
        # Get guild info from guild_settings with real names
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    guild_id,
                    COALESCE(guild_name, CONCAT('Guild ', RIGHT(guild_id, 6))) as guild_name,
                    subscription_level,
                    is_active
                FROM guild_settings 
                WHERE guild_id = %s
            """, (guild_id,))
            guild = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if guild:
                return render_template('guild_settings.html', guild=guild, guild_id=guild_id)
        
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error rendering guild settings: {e}")
        return redirect(url_for('index'))

@app.route('/guild/<int:guild_id>/subscriptions')
def subscriptions(guild_id):
    """Subscriptions page."""
    try:
        return render_template('subscriptions.html', guild_id=guild_id)
    except Exception as e:
        logger.error(f"Error rendering subscriptions: {e}")
        return render_template('subscriptions.html', guild_id=guild_id)

@app.route('/league/<int:league_id>/scores')
def live_scores_league(league_id):
    """Live scores for a specific league."""
    try:
        # Get league info and games
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Get league info
            cursor.execute("SELECT * FROM leagues WHERE league_id = %s", (league_id,))
            league = cursor.fetchone()
            
            if league:
                # Get games for this league
                cursor.execute("""
                    SELECT 
                        g.*,
                        ht.team_name as home_team_name,
                        ht.logo_url as home_logo,
                        at.team_name as away_team_name,
                        at.logo_url as away_logo
                    FROM games g
                    JOIN teams ht ON g.home_team_id = ht.team_id
                    JOIN teams at ON g.away_team_id = at.team_id
                    WHERE g.league_id = %s
                    AND g.game_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    ORDER BY g.game_time DESC
                """, (league_id,))
                games = cursor.fetchall()
                
                cursor.close()
                connection.close()
                
                return render_template('live_scores_league.html', 
                                    league=league, 
                                    games=games)
        
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error rendering league scores: {e}")
        return redirect(url_for('index'))

@app.route('/guild/<int:guild_id>/customize')
def guild_customize(guild_id):
    """Guild customization page - admin only."""
    try:
        # Check if user has admin access to this guild
        if not check_guild_admin_access(guild_id):
            return redirect(url_for('guild_home', guild_id=guild_id))
        
        # Get current customization settings
        customization = get_guild_customization(guild_id)
        
        # Get guild info
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT guild_id, guild_name, subscription_level 
                FROM guild_settings WHERE guild_id = %s
            """, (guild_id,))
            guild = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if guild:
                return render_template('guild_customize.html', 
                                    guild=guild,
                                    customization=customization,
                                    guild_id=guild_id)
        
        return redirect(url_for('guild_home', guild_id=guild_id))
        
    except Exception as e:
        logger.error(f"Error rendering guild customize page: {e}")
        return redirect(url_for('guild_home', guild_id=guild_id))


@app.route('/guild/<int:guild_id>/customize', methods=['POST'])
def update_guild_customize(guild_id):
    """Update guild customization settings."""
    try:
        # Check if user has admin access to this guild
        if not check_guild_admin_access(guild_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get form data
        settings = {}
        
        # Text fields
        text_fields = [
            'page_title', 'page_description', 'welcome_message',
            'about_section', 'features_section', 'rules_section',
            'discord_invite', 'website_url', 'twitter_url'
        ]
        
        for field in text_fields:
            if field in request.form:
                settings[field] = request.form[field].strip() or None
        
        # Color fields
        color_fields = ['primary_color', 'secondary_color', 'accent_color']
        for field in color_fields:
            if field in request.form:
                color = request.form[field].strip()
                if color and color.startswith('#') and len(color) == 7:
                    settings[field] = color
        
        # Boolean fields
        boolean_fields = ['show_leaderboard', 'show_recent_bets', 'show_stats', 'public_access']
        for field in boolean_fields:
            settings[field] = field in request.form
        
        # Update settings
        if update_guild_customization(guild_id, settings):
            return jsonify({'success': True, 'message': 'Settings updated successfully'})
        else:
            return jsonify({'error': 'Failed to update settings'}), 500
            
    except Exception as e:
        logger.error(f"Error updating guild customization: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/guild/<int:guild_id>/public')
def guild_public_page(guild_id):
    """Public guild page - no login required if public_access enabled."""
    try:
        # Get guild info and customization
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Check if guild_customization table exists
            try:
                cursor.execute("SHOW TABLES LIKE 'guild_customization'")
                table_exists = cursor.fetchone() is not None
            except:
                table_exists = False
            
            if not table_exists:
                # Demo mode - show sample guild page
                demo_guild_data = {
                    'guild_id': guild_id,
                    'guild_name': f'Demo Guild {guild_id}',
                    'subscription_level': 'free',
                    'is_active': 1,
                    'page_title': f'Demo Guild {guild_id} - Betting Hub',
                    'page_description': 'This is a demo of the guild customization system. Create your own customized page when you set up the database!',
                    'welcome_message': 'Welcome to our demo betting community!',
                    'primary_color': '#667eea',
                    'secondary_color': '#764ba2',
                    'accent_color': '#5865F2',
                    'about_section': 'This is a demonstration of the guild customization system. Guild admins can customize colors, content, and display options to create their unique betting community page.',
                    'features_section': 'Track bets, compete with friends, view detailed analytics, and manage your betting community all in one place.',
                    'rules_section': '1. Be respectful to all members\n2. No spam betting\n3. Keep discussions friendly\n4. Follow Discord ToS',
                    'discord_invite': None,
                    'website_url': None,
                    'twitter_url': None,
                    'show_leaderboard': True,
                    'show_recent_bets': True,
                    'show_stats': True,
                    'public_access': True
                }
                
                # Demo stats
                demo_stats = {
                    'total_bettors': 42,
                    'total_bets': 287,
                    'total_wins': 156,
                    'total_losses': 131,
                    'net_profit': 45.7
                }
                
                # Demo leaderboard
                demo_leaderboard = [
                    {'user_id': '123456789', 'total_bets': 45, 'wins': 28, 'losses': 17, 'win_rate': 62.2, 'net_profit': 23.5},
                    {'user_id': '987654321', 'total_bets': 38, 'wins': 22, 'losses': 16, 'win_rate': 57.9, 'net_profit': 18.2},
                    {'user_id': '456789123', 'total_bets': 31, 'wins': 19, 'losses': 12, 'win_rate': 61.3, 'net_profit': 15.8},
                    {'user_id': '789123456', 'total_bets': 29, 'wins': 16, 'losses': 13, 'win_rate': 55.2, 'net_profit': 12.1},
                    {'user_id': '321654987', 'total_bets': 26, 'wins': 14, 'losses': 12, 'win_rate': 53.8, 'net_profit': 8.9}
                ]
                
                # Demo recent activity
                demo_recent_activity = [
                    {'description': 'Lakers vs Warriors', 'result': 'won', 'profit_loss': 5.2, 'bet_date': datetime.now()},
                    {'description': 'Chiefs vs Bills', 'result': 'lost', 'profit_loss': -3.0, 'bet_date': datetime.now()},
                    {'description': 'Celtics vs Heat', 'result': 'won', 'profit_loss': 7.5, 'bet_date': datetime.now()},
                ]
                
                cursor.close()
                connection.close()
                
                return render_template('guild_public.html',
                                    guild=demo_guild_data,
                                    guild_stats=demo_stats,
                                    leaderboard=demo_leaderboard,
                                    recent_activity=demo_recent_activity,
                                    guild_id=guild_id,
                                    demo_mode=True)
            
            # Get guild and customization in one query
            cursor.execute("""
                SELECT 
                    gs.guild_id, gs.guild_name, gs.subscription_level, gs.is_active,
                    gc.*
                FROM guild_settings gs
                LEFT JOIN guild_customization gc ON gs.guild_id = gc.guild_id
                WHERE gs.guild_id = %s AND gs.is_active = 1
            """, (guild_id,))
            
            guild_data = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if not guild_data:
                return render_template('guild_not_found.html'), 404
            
            # Check if public access is enabled or user has access
            public_access = guild_data.get('public_access') if hasattr(guild_data, 'get') else getattr(guild_data, 'public_access', False)
            has_access = public_access or check_guild_access(guild_id)
            
            if not has_access:
                guild_name = guild_data.get('guild_name') if hasattr(guild_data, 'get') else getattr(guild_data, 'guild_name', 'Unknown Guild')
                return render_template('guild_private.html', guild_name=guild_name), 403
            
            # Get guild statistics (only public stats)
            guild_stats = get_guild_public_stats(guild_id)
            
            # Get leaderboard if enabled
            leaderboard = None
            show_leaderboard = guild_data.get('show_leaderboard') if hasattr(guild_data, 'get') else getattr(guild_data, 'show_leaderboard', True)
            if show_leaderboard:
                leaderboard = get_guild_leaderboard(guild_id, limit=10)
            
            # Get recent activity if enabled
            recent_activity = None
            show_recent_bets = guild_data.get('show_recent_bets') if hasattr(guild_data, 'get') else getattr(guild_data, 'show_recent_bets', True)
            if show_recent_bets:
                recent_activity = get_recent_activity(guild_id, limit=5)
            
            return render_template('guild_public.html',
                                guild=guild_data,
                                guild_stats=guild_stats,
                                leaderboard=leaderboard,
                                recent_activity=recent_activity,
                                guild_id=guild_id)
        
        return render_template('guild_not_found.html'), 404
        
    except Exception as e:
        logger.error(f"Error rendering public guild page: {e}")
        return render_template('error.html'), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'betting-bot-webapp'
    })

@app.route('/api/status')
def api_status():
    """API status endpoint."""
    return jsonify({
        'status': 'operational',
        'version': '1.0.0',
        'environment': app.config['ENV'],
        'debug': app.config['DEBUG']
    })


if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv('WEBAPP_PORT', 25594))

    # Ensure db_logs directory exists
    os.makedirs('db_logs', exist_ok=True)

    logger.info(f"Starting Flask webapp on port {port}")
    logger.info(f"Environment: {app.config['ENV']}")
    logger.info(f"Debug mode: {app.config['DEBUG']}")

    try:
        # Listen on all interfaces, on specified port
        app.run(
            host="0.0.0.0",
            port=port,
            debug=app.config['DEBUG'],
            use_reloader=False  # Disable reloader in production
        )
    except Exception as e:
        logger.error(f"Failed to start Flask webapp: {e}")
        sys.exit(1)



# Performance-optimized Discord OAuth functions
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Global session for connection pooling
_discord_session = None
_executor = ThreadPoolExecutor(max_workers=4)

def get_discord_session():
    """Get or create Discord HTTP session with connection pooling."""
    global _discord_session
    if _discord_session is None or _discord_session.closed:
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=30,  # Per-host connection limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            keepalive_timeout=60,
            enable_cleanup_closed=True
        )
        timeout = aiohttp.ClientTimeout(total=10, connect=5)
        _discord_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'DBSBM-Bot/1.0'}
        )
    return _discord_session

async def async_exchange_discord_code(code):
    """Async version of Discord code exchange with connection pooling."""
    try:
        data = {
            'client_id': os.getenv('DISCORD_CLIENT_ID'),
            'client_secret': os.getenv('DISCORD_CLIENT_SECRET'),
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': os.getenv('DISCORD_REDIRECT_URI')
        }
        
        session = get_discord_session()
        async with session.post('https://discord.com/api/oauth2/token', data=data) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Discord token exchange failed: {response.status}")
                return None
                
    except Exception as e:
        logger.error(f"Error exchanging Discord code: {e}")
        return None

async def async_get_discord_user_info(access_token):
    """Async version of Discord user info with connection pooling."""
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        session = get_discord_session()
        
        async with session.get('https://discord.com/api/users/@me', headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Discord user info failed: {response.status}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting Discord user info: {e}")
        return None

async def async_get_discord_user_guilds(access_token):
    """Async version of Discord user guilds with connection pooling."""
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        session = get_discord_session()
        
        async with session.get('https://discord.com/api/users/@me/guilds', headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Discord user guilds failed: {response.status}")
                return []
                
    except Exception as e:
        logger.error(f"Error getting Discord user guilds: {e}")
        return []

def run_async_discord_auth(code):
    """Run async Discord auth operations concurrently."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Step 1: Exchange code for token
        token_data = loop.run_until_complete(async_exchange_discord_code(code))
        if not token_data or 'access_token' not in token_data:
            return None, None, []
        
        access_token = token_data['access_token']
        
        # Step 2: Get user info and guilds concurrently
        user_info_task = async_get_discord_user_info(access_token)
        user_guilds_task = async_get_discord_user_guilds(access_token)
        
        user_info, user_guilds = loop.run_until_complete(
            asyncio.gather(user_info_task, user_guilds_task)
        )
        
        return token_data, user_info, user_guilds
        
    finally:
        loop.close()

# Performance-optimized callback function
def discord_callback_optimized():
    """Optimized Discord OAuth callback with concurrent requests."""
    start_time = time.time()
    
    code = request.args.get('code')
    if not code:
        logger.warning("No code in Discord callback")
        return redirect(url_for('index'))
    
    # Run all Discord API calls concurrently
    token_data, user_info, user_guilds = run_async_discord_auth(code)
    
    if not user_info:
        logger.error("Failed to get Discord user info")
        return redirect(url_for('index'))
    
    # Get accessible guilds (optimize this with caching)
    accessible_guilds = get_user_accessible_guilds_cached(user_guilds)
    
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
    logger.info(f"Discord auth completed in {auth_time:.2f}s")
    
    # Redirect based on accessible guilds
    if accessible_guilds:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('subscribe'))

# Cache for bot guild list (refresh every 5 minutes)
_bot_guilds_cache = {'data': None, 'timestamp': 0}
BOT_GUILDS_CACHE_TTL = 300  # 5 minutes

def get_bot_guilds_cached():
    """Get bot guilds with caching to reduce database hits."""
    global _bot_guilds_cache
    
    current_time = time.time()
    if (_bot_guilds_cache['data'] is None or 
        current_time - _bot_guilds_cache['timestamp'] > BOT_GUILDS_CACHE_TTL):
        
        # Refresh cache
        _bot_guilds_cache['data'] = get_bot_guilds()
        _bot_guilds_cache['timestamp'] = current_time
        logger.info("Bot guilds cache refreshed")
    
    return _bot_guilds_cache['data']

def get_user_accessible_guilds_cached(user_guilds):
    """Optimized version with caching."""
    if not user_guilds:
        return []
    
    # Get bot guilds from cache
    bot_guilds = get_bot_guilds_cached()
    if not bot_guilds:
        return []
    
    # Convert to set for O(1) lookup
    bot_guild_ids = {str(guild['guild_id']) for guild in bot_guilds}
    
    # Filter user guilds
    accessible = []
    for guild in user_guilds:
        if str(guild['id']) in bot_guild_ids:
            accessible.append({
                'id': guild['id'],
                'name': guild['name'],
                'icon': guild.get('icon'),
                'permissions': guild.get('permissions', 0)
            })
    
    return accessible
