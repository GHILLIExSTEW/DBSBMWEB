#!/usr/bin/env python3
"""
Windows Service Version of Flask Application
Runs continuously as a scheduled task with auto-restart capability
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add the application directory to Python path
app_dir = Path(__file__).parent / 'cgi-bin'
sys.path.insert(0, str(app_dir))

# Set up logging
log_file = Path(__file__).parent / 'flask_service.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def setup_environment():
    """Set up the production environment."""
    env_file = app_dir / '.env'
    
    if env_file.exists():
        logging.info(f"✅ Using environment file: {env_file}")
        return True
    else:
        logging.error("❌ .env file not found in cgi-bin directory!")
        return False

def start_flask_app():
    """Start the Flask application with error handling."""
    try:
        # Change to the cgi-bin directory
        os.chdir(app_dir)
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv('.env')
        
        # Import and configure the Flask app
        from webapp import app
        
        logging.info("🚀 Starting Flask server as Windows service...")
        logging.info("🌐 Server will be accessible at: http://YOUR_LIGHTSAIL_IP:5000")
        
        # Run Flask in production mode
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True,
            use_reloader=False  # Important: Disable reloader for service mode
        )
        
    except Exception as e:
        logging.error(f"❌ Flask server error: {e}")
        raise

def main_service_loop():
    """Main service loop with auto-restart capability."""
    max_restarts = 10
    restart_count = 0
    
    while restart_count < max_restarts:
        try:
            logging.info(f"🔄 Starting Flask service (attempt {restart_count + 1})")
            
            # Setup environment
            if not setup_environment():
                logging.error("Environment setup failed, exiting...")
                break
            
            # Start Flask app
            start_flask_app()
            
        except KeyboardInterrupt:
            logging.info("🛑 Service stopped by user (Ctrl+C)")
            break
        except Exception as e:
            restart_count += 1
            logging.error(f"💥 Service crashed: {e}")
            
            if restart_count < max_restarts:
                wait_time = min(30 * restart_count, 300)  # Exponential backoff, max 5 minutes
                logging.info(f"⏰ Restarting in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logging.error(f"💀 Max restarts ({max_restarts}) reached. Service stopping.")
                break
    
    logging.info("🏁 Flask service ended")

if __name__ == '__main__':
    # Create a simple argument parser
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            # Test mode - run once and exit
            logging.info("🧪 Running in test mode...")
            setup_environment()
            start_flask_app()
        elif sys.argv[1] == 'service':
            # Service mode - run with auto-restart
            logging.info("🔧 Running in service mode...")
            main_service_loop()
    else:
        # Default mode
        logging.info("🚀 Running Flask service...")
        main_service_loop()
