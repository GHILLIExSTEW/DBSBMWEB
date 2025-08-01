#/usr/bin/env python3
import os
import sys
import cgitb
cgitb.enable()

print("Content-Type: text/html")
print()
print("""^
<DOCTYPE html>
<html>
<head>
    <title>Deployment Test</title>
</head>
<body>
    <h1>✅ Deployment Successful</h1>
    <p>Your Flask web app is now deployed on Bluehost.</p>
    <p><a href="/cgi-bin/flask_cgi.py">Test Flask App</a></p>
    <p><a href="/cgi-bin/test_cgi.py">Test CGI</a></p>
</body>
</html>
"""^)
