# Guild Customization System Setup Guide

## Overview
This system allows each Discord guild to have their own customizable webpage that's automatically generated when the bot joins a server. Guild admins can customize colors, content, images, and settings through an easy-to-use interface.

## Features

### 🎨 **Customization Options**
- **Colors & Branding**: Primary, secondary, and accent colors
- **Content Sections**: About, features, rules, welcome message
- **Images**: Logo, hero image, background
- **Social Links**: Discord invite, website, Twitter
- **Display Options**: Show/hide leaderboard, recent bets, stats
- **Public Access**: Allow anyone to view the guild page

### 🔗 **URL Structure**
- Guild Admin Panel: `/guild/{guild_id}/customize`
- Public Guild Page: `/guild/{guild_id}/public`
- Private Guild Page: `/guild/{guild_id}` (requires login)

## Setup Instructions

### 1. Database Setup
Run the SQL schema to create the required tables:

```bash
mysql -u your_username -p your_database < guild_customization_schema.sql
```

### 2. Create Upload Directory
Create a directory for guild images:

```bash
mkdir -p cgi-bin/bot/static/guild_images
chmod 755 cgi-bin/bot/static/guild_images
```

### 3. Update Guild Settings Template
Add a "Customize Page" button to your existing `guild_settings.html`:

```html
<a href="{{ url_for('guild_customize', guild_id=guild.guild_id) }}" 
   class="btn btn-primary">
    <i class="fas fa-palette"></i> Customize Page
</a>
```

### 4. Bot Integration
When your Discord bot joins a new server, automatically create default customization:

```python
# In your bot's on_guild_join event
def on_guild_join(guild):
    create_default_guild_customization(guild.id, guild.name)
```

## Usage Guide

### For Guild Admins
1. **Access Customization**: Go to `/guild/{guild_id}/customize`
2. **Edit Settings**: Modify colors, text, and display options
3. **Upload Images**: Add logo, hero image, or background
4. **Preview Changes**: Use the preview button to see changes
5. **Save**: Click "Save Changes" to apply updates
6. **Share**: Enable "Public Access" to share your guild page

### For Guild Members
1. **Access Private Page**: Go to `/guild/{guild_id}` (requires Discord login)
2. **View Public Page**: Go to `/guild/{guild_id}/public` (if public access enabled)

## Customization Options Explained

### 🎨 Colors & Branding
- **Primary Color**: Main brand color used for headings and accents
- **Secondary Color**: Used in gradients and secondary elements  
- **Accent Color**: Used for buttons and interactive elements

### 📝 Content Sections
- **Page Title**: Shown in browser tab and page header
- **Welcome Message**: Greeting displayed prominently
- **Page Description**: Meta description and subtitle
- **About Section**: Detailed description of your guild
- **Features Section**: Highlight what makes your guild special
- **Rules Section**: Betting rules and guidelines

### 🖼️ Images
- **Logo**: Small guild logo (recommended: 200x200px)
- **Hero Image**: Large promotional image (recommended: 800x400px)
- **Background**: Background image for hero section (recommended: 1920x1080px)

### 🔗 Social Links
- **Discord Invite**: Permanent invite link to your Discord server
- **Website**: Your guild's website or additional resources
- **Twitter**: Your guild's Twitter account

### 👁️ Display Options
- **Show Leaderboard**: Display top performers
- **Show Recent Bets**: Show recent betting activity
- **Show Statistics**: Display guild betting statistics
- **Public Access**: Allow non-members to view the page

## Technical Details

### Database Tables
- `guild_customization`: Stores all customization settings
- `guild_images`: Manages uploaded images and media
- `guild_page_templates`: Predefined page templates

### File Structure
```
cgi-bin/
├── bot/
│   ├── static/
│   │   └── guild_images/           # Uploaded guild images
│   └── templates/
│       ├── guild_customize.html    # Admin customization interface
│       ├── guild_public.html       # Public guild page
│       ├── guild_not_found.html    # 404 error page
│       └── guild_private.html      # Private access error
├── webapp.py                       # Main application with new routes
└── guild_customization_schema.sql  # Database schema
```

### Security Features
- **Admin Access Control**: Only guild admins can modify settings
- **File Upload Validation**: Images are validated for type and size
- **SQL Injection Protection**: All queries use parameterized statements
- **XSS Prevention**: All user content is properly escaped

## Example Usage

### Creating a Custom Guild Page
1. Guild admin navigates to `/guild/123456789/customize`
2. Sets colors to match their brand
3. Uploads their guild logo and a hero image
4. Writes a welcome message and about section
5. Enables public access
6. Saves changes

### Sharing the Guild Page
- **Public URL**: `yourdomain.com/guild/123456789/public`
- **Shareable on social media, websites, or Discord**
- **No login required for visitors**

## Future Enhancements

### Potential Features
- **Custom CSS**: Allow advanced users to add custom styling
- **Image Gallery**: Multiple images in a carousel
- **Member Showcase**: Highlight top members with photos
- **Custom Domains**: Allow guilds to use their own subdomain
- **Analytics**: Track page views and visitor engagement
- **Templates**: Pre-designed themes for different guild types
- **Embeds**: Rich Discord embeds for sharing
- **API Integration**: Connect with external betting platforms

### Template System
The system supports multiple page templates:
- **Modern**: Gradient design with animations (default)
- **Classic**: Clean, traditional layout
- **Gaming**: Dark theme optimized for gaming communities

## Support

### Common Issues
1. **Images not displaying**: Check file permissions on `guild_images` directory
2. **Colors not updating**: Clear browser cache after changes
3. **Access denied**: Verify user has admin permissions in Discord guild
4. **Database errors**: Ensure all tables are created and user has proper permissions

### Troubleshooting
- Check the webapp logs for detailed error messages
- Verify Discord OAuth permissions include guild management
- Ensure database connection is working properly
- Test with a simple guild customization first

This system provides a powerful way for Discord communities to create their own branded betting hub pages, fostering community engagement and professional presentation.
