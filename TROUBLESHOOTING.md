# 🚨 Production Server Troubleshooting Guide

## Current Issue: 500 Internal Server Error

You're getting a 500 error at `https://bet-tracking-ai.com/cgi-bin/flask_cgi.py`

## Step-by-Step Fix Process

### Step 1: Fix Environment File ✅ COMPLETED
- [x] Fixed corrupted `.env` file with proper formatting
- [x] Set production environment (`FLASK_ENV=production`, `FLASK_DEBUG=false`)
- [x] Configured correct Discord redirect URI

### Step 2: Test Basic CGI Functionality

**Upload and test this simple CGI script first:**

1. Upload `test_cgi_simple.py` to your server's cgi-bin directory
2. Set executable permissions: `chmod +x test_cgi_simple.py`
3. Test at: `https://bet-tracking-ai.com/cgi-bin/test_cgi_simple.py`

**Expected Result:** Should show system information page
**If this fails:** CGI is not properly configured on your server

### Step 3: Common Fixes for 500 Errors

#### A. File Permissions
```bash
chmod +x flask_cgi.py
chmod +x test_cgi_simple.py
chmod 644 .env
chmod 644 webapp.py
```

#### B. Python Path Issues
Make sure Python 3 is available and modules can be imported:
```bash
python3 --version
python3 -c "import flask"
```

#### C. Missing Dependencies
Your server needs these Python packages:
```
flask
python-dotenv
mysql-connector-python
requests
```

### Step 4: Use Simplified CGI Script

I've created `flask_cgi_simple.py` with better error handling:

1. Upload `flask_cgi_simple.py` to your cgi-bin directory
2. Set permissions: `chmod +x flask_cgi_simple.py`
3. Test at: `https://bet-tracking-ai.com/cgi-bin/flask_cgi_simple.py`

### Step 5: Check Server Logs

Look for error details in your hosting provider's error logs:
- cPanel → Error Logs
- Look for Python import errors
- Check for permission denied errors

## Quick Diagnostics

### Test 1: Basic CGI
**URL:** `https://bet-tracking-ai.com/cgi-bin/test_cgi_simple.py`
**Expected:** System information page
**If fails:** CGI not working

### Test 2: Simple Flask App
**URL:** `https://bet-tracking-ai.com/cgi-bin/flask_cgi_simple.py`
**Expected:** Flask app or detailed error message
**If fails:** Python/Flask issues

### Test 3: Full App
**URL:** `https://bet-tracking-ai.com/cgi-bin/flask_cgi.py`
**Expected:** Your full application
**If fails:** App-specific issues

## Alternative: Direct Server Approach

If CGI continues to have issues, use the direct server:

1. **SSH into your server**
2. **Navigate to your directory**
3. **Run directly:**
   ```bash
   cd /path/to/cgi-bin
   python3 webapp.py
   ```
4. **Access via:** `http://50.6.19.162:25595`

## Most Common Issues & Solutions

### Issue 1: "No module named 'flask'"
**Solution:** Install Flask on the server
```bash
pip3 install flask python-dotenv mysql-connector-python requests
```

### Issue 2: "Permission denied"
**Solution:** Fix file permissions
```bash
chmod +x *.py
```

### Issue 3: "Import error: webapp"
**Solution:** Ensure webapp.py is in the same directory and has correct syntax

### Issue 4: "Database connection error"
**Solution:** This is expected initially - the app should still load with demo mode

### Issue 5: "Environment variables not found"
**Solution:** Ensure .env file is properly formatted (already fixed)

## Current File Status

### ✅ Fixed Files
- [x] `.env` - Fixed formatting and production settings
- [x] `flask_cgi_simple.py` - New simplified CGI wrapper
- [x] `test_cgi_simple.py` - Basic CGI test script

### 📁 Files to Upload
1. `test_cgi_simple.py` (test basic CGI)
2. `flask_cgi_simple.py` (simplified Flask wrapper)
3. `.env` (fixed environment file)
4. `webapp.py` (main Flask app)
5. `bot/` directory (templates and static files)

### 🔧 Commands to Run on Server
```bash
# Set permissions
chmod +x test_cgi_simple.py
chmod +x flask_cgi_simple.py
chmod +x flask_cgi.py
chmod 644 .env

# Test Python
python3 --version
python3 -c "import flask; print('Flask OK')"
```

## Next Steps

1. **Upload the test script and try it first**
2. **Check your server's error logs for specific error messages**
3. **If test script works, try the simplified Flask wrapper**
4. **Contact your hosting provider if CGI itself isn't working**

## Contact Information

If you need to contact support:
- **Hosting Provider:** For CGI configuration issues
- **Error Logs:** Check cPanel or hosting control panel
- **Python Environment:** May need to request Python 3 and Flask installation

## Testing URLs

After uploading files, test in this order:

1. `https://bet-tracking-ai.com/cgi-bin/test_cgi_simple.py` (basic test)
2. `https://bet-tracking-ai.com/cgi-bin/flask_cgi_simple.py` (Flask test)
3. `https://bet-tracking-ai.com/cgi-bin/flask_cgi.py` (full app)

Each step should provide better error information to help diagnose the issue!
