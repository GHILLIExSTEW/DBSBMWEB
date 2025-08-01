#!/usr/bin/env python3
import os
import sys
import cgitb
cgitb.enable()

print("Content-Type: text/html")
print()
print("""
<!DOCTYPE html>
<html>
<head>
    <title>Server Test</title>
</head>
<body>
    <h1>✅ Server is Working!</h1>
    <p>If you can see this page, the server is working correctly.</p>
    <p>Now let's test the Flask app...</p>
    <a href="/cgi-bin/webapp.py/health">Test Flask Health Endpoint</a>
</body>
</html>
""") 