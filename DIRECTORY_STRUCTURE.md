# Directory Structure Guide

## Project Layout

This repository maintains a specific directory structure for the Flask Discord bot web application:

```
bet-tracking-ai/
├── cgi-bin/                    # Main application directory
│   ├── bot/                    # Bot web interface
│   │   ├── static/             # Static web assets
│   │   │   ├── css/            # CSS stylesheets
│   │   │   ├── images/         # Static images
│   │   │   ├── js/             # JavaScript files
│   │   │   └── guild_images/   # Guild custom uploads
│   │   └── templates/          # Jinja2 HTML templates
│   ├── db_logs/                # Application logs
│   ├── *.py                    # Python application files
│   └── *.sql                   # Database schema files
├── docs/                       # Documentation
├── *.md                        # Project documentation
└── requirements.txt            # Python dependencies
```

## Directory Purposes

### `cgi-bin/bot/`
Contains the web interface components:
- **static/**: Web assets (CSS, JS, images)
- **templates/**: Jinja2 HTML templates for pages

### `cgi-bin/db_logs/`
Application logging directory:
- Daily rotating log files
- Error and debug information
- Production monitoring data

### `cgi-bin/bot/static/guild_images/`
User-uploaded content:
- Custom guild logos and banners
- Guild-specific images
- Uploaded by guild administrators

## .gitkeep Files

This repository uses `.gitkeep` files to ensure important directories are tracked by git even when empty:

- **Why needed**: Git doesn't track empty directories
- **Benefit**: Maintains project structure for new clones
- **Location**: In every important directory that might become empty

## Development Notes

### Adding New Directories
When adding new directories that should be preserved:
1. Create the directory
2. Add a `.gitkeep` file with a descriptive comment
3. Update `.gitignore` if the directory should exclude content but preserve structure

### File Upload Directories
Directories like `guild_images/` are configured to:
- Preserve the directory structure (via `.gitkeep`)
- Exclude uploaded content (via `.gitignore`)
- Allow for clean deployment without user data

## Deployment Benefits

This structure ensures:
- **Clean deployments**: Required directories exist
- **Clear organization**: Developers understand the layout
- **File upload ready**: Upload directories are pre-created
- **Log management**: Log directory exists for application startup
