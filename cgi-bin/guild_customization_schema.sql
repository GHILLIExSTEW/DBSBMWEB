-- Guild Customization Schema Extension
-- Add these tables to your existing database

-- Guild Customization Settings
CREATE TABLE IF NOT EXISTS guild_customization (
    id INT AUTO_INCREMENT PRIMARY KEY,
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_guild (guild_id),
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE
);

-- Guild Custom Images
CREATE TABLE IF NOT EXISTS guild_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    image_type ENUM('hero', 'logo', 'background', 'gallery') NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size INT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    alt_text VARCHAR(255) DEFAULT NULL,
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    uploaded_by BIGINT DEFAULT NULL, -- Discord user ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_guild_type (guild_id, image_type),
    FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id) ON DELETE CASCADE
);

-- Guild Page Templates
CREATE TABLE IF NOT EXISTS guild_page_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL,
    template_description TEXT,
    template_config JSON NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_template_name (template_name)
);

-- Insert default templates
INSERT INTO guild_page_templates (template_name, template_description, template_config, is_default) VALUES 
('modern', 'Modern design with gradients and animations', '{"layout": "hero-stats-leaderboard", "style": "modern", "animations": true}', TRUE),
('classic', 'Clean classic design', '{"layout": "header-content-sidebar", "style": "classic", "animations": false}', FALSE),
('gaming', 'Gaming-focused design with dark theme', '{"layout": "full-width", "style": "gaming", "animations": true}', FALSE);
