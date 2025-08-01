# 🎰 Bet Tracking AI - Discord Bot Web System

A comprehensive Discord bot and web application for managing betting communities, live sports tracking, and guild customization.

## 🌟 Features

### 🤖 Discord Bot Integration
- **Slash Commands** for betting management
- **Live Sports Data** integration
- **Guild-Specific Customization** for each Discord server
- **OAuth2 Authentication** for seamless user experience

### 🌐 Web Application
- **Subscription Landing Page** with modern UI
- **Guild Public Pages** - Each Discord server gets its own webpage
- **Admin Customization Panel** for guild administrators
- **Live Sports Scores** and betting odds integration
- **User Dashboard** with betting statistics

### 🎨 Guild Customization System
- **Auto-Generated Pages** when bot joins a Discord server
- **Custom Branding** - Upload logos, banners, set colors
- **Social Links** - Discord invites, websites, social media
- **Admin-Only Access** with Discord permission verification

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL/MariaDB database
- Discord Application (Bot + OAuth2)
- Web hosting with CGI support (or VPS for direct hosting)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/GHILLIExSTEW/DBSBMWEB.git
   cd DBSBMWEB
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp cgi-bin/.env.example cgi-bin/.env
   # Edit .env with your configuration
   ```

4. **Set up database**
   ```bash
   # Import the database schema
   mysql -u username -p database_name < cgi-bin/guild_customization_schema.sql
   ```

5. **Configure Discord Application**
   - Create Discord application at https://discord.com/developers/applications
   - Set up OAuth2 redirect URIs
   - Configure bot permissions
   - See `DISCORD_PERMISSIONS_GUIDE.md` for details

### Deployment Options

#### Option 1: CGI Hosting (Recommended for shared hosting)
```bash
# Upload files to your web server's cgi-bin directory
# Set permissions
chmod +x cgi-bin/flask_cgi.py
# Access via: https://yourdomain.com/cgi-bin/flask_cgi.py
```

#### Option 2: Direct Server (VPS/Dedicated)
```bash
cd cgi-bin
python webapp.py
# Access via: http://your-server-ip:25595
```

## 📁 Project Structure

```
bet-tracking-ai/
├── cgi-bin/                    # Main application directory
│   ├── webapp.py              # Flask application
│   ├── flask_cgi.py           # CGI wrapper for web hosting
│   ├── .env.example           # Environment variables template
│   ├── bot/
│   │   ├── static/            # CSS, JS, images
│   │   └── templates/         # Jinja2 HTML templates
│   ├── guild_customization_schema.sql  # Database schema
│   └── requirements.txt       # Python dependencies
├── docs/                      # Documentation
├── DEPLOYMENT_CHECKLIST.md    # Deployment guide
├── TROUBLESHOOTING.md         # Common issues and fixes
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

Copy `cgi-bin/.env.example` to `cgi-bin/.env` and configure:

```properties
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=your-secure-secret-key

# Database
MYSQL_HOST=your-database-host
MYSQL_USER=your-database-user
MYSQL_PASSWORD=your-database-password
MYSQL_DB=your-database-name

# Discord OAuth
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret
DISCORD_REDIRECT_URI=https://yourdomain.com/cgi-bin/flask_cgi.py/auth/discord/callback
DISCORD_BOT_TOKEN=your-bot-token
```

### Discord Application Setup

1. **Create Discord App**: https://discord.com/developers/applications
2. **Configure OAuth2**: Add redirect URIs for your domain
3. **Set Bot Permissions**: Use the comprehensive permission set (see guide)
4. **Get Credentials**: Client ID, Client Secret, Bot Token

## 📖 Documentation

- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[Discord Permissions Guide](cgi-bin/DISCORD_PERMISSIONS_GUIDE.md)** - Discord setup details
- **[Guild Customization Guide](cgi-bin/GUILD_CUSTOMIZATION_GUIDE.md)** - Feature documentation
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions

## 🌐 Live Demo

### Web Pages
- **Landing Page**: Modern subscription interface with pricing tiers
- **Server List**: Public directory of Discord communities
- **Guild Pages**: Custom pages for each Discord server (demo mode available)

### Discord Bot Features
- **Betting Commands**: Comprehensive slash command system
- **Live Sports**: Real-time scores and odds integration
- **Guild Management**: Admin tools for community management

## 🛠 Development

### Local Development Setup

1. **Clone and install dependencies**
2. **Set up local database** (MySQL or SQLite for testing)
3. **Configure Discord app** with local redirect URI
4. **Run development server**:
   ```bash
   cd cgi-bin
   python webapp.py
   ```
5. **Access locally**: http://127.0.0.1:25595

### Adding Features

The application is built with a modular structure:
- **Routes**: Add new endpoints in `webapp.py`
- **Templates**: Create Jinja2 templates in `bot/templates/`
- **Static Assets**: Add CSS/JS/images to `bot/static/`
- **Database**: Extend schema in `guild_customization_schema.sql`

## 🔒 Security Features

- **Discord OAuth2** integration for secure authentication
- **Admin Permission Verification** using Discord API
- **Environment Variable Protection** for sensitive data
- **Production-Ready Configuration** with debug mode controls
- **HTTPS Support** for production deployments

## 📊 Database Schema

The system uses MySQL/MariaDB with tables for:
- **Guild Customization**: Store page settings per Discord server
- **Guild Images**: Custom uploads and branding assets
- **Page Templates**: Reusable page layouts and themes
- **User Sessions**: Discord authentication state

## 🚀 Deployment Environments

### Supported Hosting Types
- **Shared Hosting** (via CGI) - Most web hosts
- **VPS/Cloud Servers** (direct Flask) - AWS, DigitalOcean, etc.
- **Container Deployment** (Docker support planned)

### Production Checklist
- [ ] Environment variables configured
- [ ] Database schema imported
- [ ] Discord application configured
- [ ] File permissions set correctly
- [ ] HTTPS enabled (recommended)
- [ ] Error logging configured

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Issues**: Open a GitHub issue for bugs or feature requests
- **Documentation**: Check the docs/ directory for detailed guides
- **Discord**: [Join our support server](https://discord.gg/your-invite) (coming soon)

### Common Issues
- **500 Internal Server Error**: Check file permissions and Python environment
- **Discord OAuth Errors**: Verify redirect URIs match exactly
- **Database Connection Issues**: Confirm credentials and network access

## 🎯 Roadmap

### Current Features (v1.0)
- ✅ Discord OAuth2 integration
- ✅ Guild customization system
- ✅ Modern web interface
- ✅ CGI and direct server deployment
- ✅ Demo mode for testing

### Planned Features (v2.0)
- 🔄 Live betting integration
- 🔄 Advanced analytics dashboard
- 🔄 Mobile-responsive improvements
- 🔄 API endpoints for external integration
- 🔄 Docker containerization

### Future Enhancements (v3.0+)
- 🔮 Machine learning betting predictions
- 🔮 Multi-language support
- 🔮 Advanced role management
- 🔮 Webhook integrations
- 🔮 Mobile app companion

---

**Built with ❤️ for the Discord betting community**

For detailed setup instructions, see the [Deployment Guide](docs/DEPLOYMENT_GUIDE.md).
