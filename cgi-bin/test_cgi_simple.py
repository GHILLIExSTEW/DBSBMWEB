#!/usr/bin/env python3
import os
import sys
import cgitb

# Enable CGI debugging
cgitb.enable()

print("Content-Type: text/html")
print()

print("""
<!DOCTYPE html>
<html>
<head>
    <title>CGI Test - Bet Tracking AI</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .success { background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; }
        .info { background: #f8f9fa; padding: 15px; margin-top: 15px; border-radius: 5px; }
        table { border-collapse: collapse; width: 100%; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="success">
        <h2>✅ CGI Test Successful</h2>
        <p>Python CGI is working correctly!</p>
    </div>
    
    <div class="info">
        <h3>System Information</h3>
        <table>
""")

# System information
info_items = [
    ("Python Version", sys.version),
    ("Python Executable", sys.executable),
    ("Current Working Directory", os.getcwd()),
    ("Script Directory", os.path.dirname(os.path.abspath(__file__))),
    ("Environment Type", os.environ.get('FLASK_ENV', 'not set')),
    ("Debug Mode", os.environ.get('FLASK_DEBUG', 'not set')),
]

for key, value in info_items:
    print(f"<tr><th>{key}</th><td>{value}</td></tr>")

print("""
        </table>
    </div>
    
    <div class="info">
        <h3>Python Path</h3>
        <ul>
""")

for path in sys.path[:10]:  # Show first 10 paths
    print(f"<li>{path}</li>")

print("""
        </ul>
    </div>
    
    <div class="info">
        <h3>Environment Variables</h3>
        <table>
""")

# Key environment variables
env_keys = ['PATH_INFO', 'QUERY_STRING', 'REQUEST_METHOD', 'HTTP_HOST', 'SERVER_NAME', 'SCRIPT_NAME']
for key in env_keys:
    value = os.environ.get(key, 'not set')
    print(f"<tr><th>{key}</th><td>{value}</td></tr>")

print("""
        </table>
    </div>
    
    <div class="info">
        <h3>File System Check</h3>
        <ul>
""")

# Check for important files
current_dir = os.path.dirname(os.path.abspath(__file__))
files_to_check = ['webapp.py', '.env', 'bot/templates', '../../../StaticFiles/DBSBMWEB/static']

for filename in files_to_check:
    filepath = os.path.join(current_dir, filename)
    if os.path.exists(filepath):
        file_type = "directory" if os.path.isdir(filepath) else "file"
        print(f"<li>✅ {filename} ({file_type}) - Found</li>")
    else:
        print(f"<li>❌ {filename} - Missing</li>")

print("""
        </ul>
    </div>
</body>
</html>
""")
