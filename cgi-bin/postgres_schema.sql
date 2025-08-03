-- Discord Bot Web System - PostgreSQL Schema
-- Complete database schema for Discord bot guild management

-- Main guild settings table
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id BIGINT PRIMARY KEY,
    guild_name VARCHAR(255) NOT NULL,
    owner_id BIGINT NOT NULL,
    prefix VARCHAR(10) DEFAULT '!',
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table for Discord users
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    discriminator VARCHAR(10),
    avatar_hash VARCHAR(255),
    is_bot BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Guild members
CREATE TABLE IF NOT EXISTS guild_members (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    nickname VARCHAR(255),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE,
    
    UNIQUE(guild_id, user_id),
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Betting/Sports related tables
CREATE TABLE IF NOT EXISTS leagues (
    league_id SERIAL PRIMARY KEY,
    league_name VARCHAR(255) NOT NULL,
    sport_type VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS teams (
    team_id SERIAL PRIMARY KEY,
    team_name VARCHAR(255) NOT NULL,
    team_code VARCHAR(10),
    league_id INTEGER,
    logo_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (league_id) REFERENCES leagues(league_id)
);

CREATE TABLE IF NOT EXISTS games (
    game_id SERIAL PRIMARY KEY,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    league_id INTEGER NOT NULL,
    game_date TIMESTAMP NOT NULL,
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    game_status VARCHAR(20) DEFAULT 'scheduled',
    season VARCHAR(20),
    week_number INTEGER,
    
    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (league_id) REFERENCES leagues(league_id)
);

-- Betting tables
CREATE TABLE IF NOT EXISTS bets (
    bet_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    game_id INTEGER NOT NULL,
    bet_type VARCHAR(50) NOT NULL, -- 'spread', 'moneyline', 'over_under'
    bet_amount DECIMAL(10,2) NOT NULL,
    bet_odds DECIMAL(8,2),
    predicted_winner INTEGER, -- team_id for winner bets
    predicted_score_home INTEGER,
    predicted_score_away INTEGER,
    bet_status VARCHAR(20) DEFAULT 'active', -- 'active', 'won', 'lost', 'cancelled'
    placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE
);

-- Guild Customization Settings
CREATE TABLE IF NOT EXISTS guild_customization (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    
    -- Page Settings
    page_title VARCHAR(255) DEFAULT NULL,
    page_description TEXT DEFAULT NULL,
    welcome_message TEXT DEFAULT NULL,
    
    -- Colors & Branding
    primary_color VARCHAR(7) DEFAULT '#667eea',
    secondary_color VARCHAR(7) DEFAULT '#764ba2',
    accent_color VARCHAR(7) DEFAULT '#5865F2',
    
    -- Images
    hero_image VARCHAR(255) DEFAULT NULL,
    logo_image VARCHAR(255) DEFAULT NULL,
    background_image VARCHAR(255) DEFAULT NULL,
    
    -- Content Sections
    about_section TEXT DEFAULT NULL,
    features_section TEXT DEFAULT NULL,
    rules_section TEXT DEFAULT NULL,
    
    -- Social Links
    discord_invite VARCHAR(255) DEFAULT NULL,
    website_url VARCHAR(255) DEFAULT NULL,
    twitter_url VARCHAR(255) DEFAULT NULL,
    
    -- Display Options
    show_leaderboard BOOLEAN DEFAULT TRUE,
    show_recent_bets BOOLEAN DEFAULT TRUE,
    show_stats BOOLEAN DEFAULT TRUE,
    public_access BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(guild_id),
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE
);

-- Guild Custom Images
CREATE TABLE IF NOT EXISTS guild_images (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    image_type VARCHAR(20) NOT NULL CHECK (image_type IN ('hero', 'logo', 'background', 'gallery')),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    alt_text VARCHAR(255) DEFAULT NULL,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    uploaded_by BIGINT DEFAULT NULL, -- Discord user ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE
);

-- Guild Page Templates
CREATE TABLE IF NOT EXISTS guild_page_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL,
    template_description TEXT,
    template_config JSONB NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(template_name)
);

-- User Statistics
CREATE TABLE IF NOT EXISTS user_stats (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    total_bets INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    total_wagered DECIMAL(12,2) DEFAULT 0.00,
    total_winnings DECIMAL(12,2) DEFAULT 0.00,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    accuracy_percentage DECIMAL(5,2) DEFAULT 0.00,
    last_bet_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(guild_id, user_id),
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_guild_settings_active ON guild_settings(is_active);
CREATE INDEX IF NOT EXISTS idx_guild_members_guild ON guild_members(guild_id);
CREATE INDEX IF NOT EXISTS idx_guild_members_user ON guild_members(user_id);
CREATE INDEX IF NOT EXISTS idx_bets_guild ON bets(guild_id);
CREATE INDEX IF NOT EXISTS idx_bets_user ON bets(user_id);
CREATE INDEX IF NOT EXISTS idx_bets_game ON bets(game_id);
CREATE INDEX IF NOT EXISTS idx_bets_status ON bets(bet_status);
CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date);
CREATE INDEX IF NOT EXISTS idx_games_league ON games(league_id);
CREATE INDEX IF NOT EXISTS idx_guild_images_guild_type ON guild_images(guild_id, image_type);
CREATE INDEX IF NOT EXISTS idx_user_stats_guild ON user_stats(guild_id);

-- Insert default templates
INSERT INTO guild_page_templates (template_name, template_description, template_config, is_default) VALUES 
('modern', 'Modern design with gradients and animations', '{"layout": "hero-stats-leaderboard", "style": "modern", "animations": true}', TRUE),
('classic', 'Clean classic design', '{"layout": "header-content-sidebar", "style": "classic", "animations": false}', FALSE),
('gaming', 'Gaming-focused design with dark theme', '{"layout": "full-width", "style": "gaming", "animations": true}', FALSE)
ON CONFLICT (template_name) DO NOTHING;

-- Insert some sample leagues
INSERT INTO leagues (league_name, sport_type) VALUES 
('NFL', 'American Football'),
('NBA', 'Basketball'),
('MLB', 'Baseball'),
('NHL', 'Hockey'),
('Premier League', 'Soccer'),
('Champions League', 'Soccer')
ON CONFLICT DO NOTHING;
