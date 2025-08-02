#!/usr/bin/env python3
"""
Flask Server Watchdog - Ensures the Flask server never stays down
This script continuously monitors the Flask server and restarts it if it goes down.
"""
import os
import sys
import time
import subprocess
import requests
import logging
import signal
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] Watchdog: %(message)s',
    handlers=[
        logging.FileHandler('db_logs/watchdog.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FlaskWatchdog:
    def __init__(self):
        self.server_process = None
        self.server_script = "c:\\Users\\Administrator\\Desktop\\DBSBMWEB\\cgi-bin\\production_server.py"
        self.python_exe = "C:/Users/Administrator/Desktop/DBSBMWEB/.venv/Scripts/python.exe"
        self.server_url = "http://localhost:25595/health"
        self.check_interval = 10  # Check every 10 seconds
        self.restart_delay = 5    # Wait 5 seconds before restart
        self.max_restart_attempts = 5
        self.restart_count = 0
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down watchdog...")
        self.running = False
        if self.server_process:
            self.stop_server()

    def is_server_healthy(self):
        """Check if the Flask server is responding to health checks."""
        try:
            response = requests.get(self.server_url, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def start_server(self):
        """Start the Flask server process."""
        try:
            logger.info("Starting Flask server...")
            
            # Change to the correct directory
            cwd = "c:\\Users\\Administrator\\Desktop\\DBSBMWEB\\cgi-bin"
            
            # Start the server process
            self.server_process = subprocess.Popen(
                [self.python_exe, self.server_script],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            # Wait a moment for server to start
            time.sleep(3)
            
            # Check if process is still running
            if self.server_process.poll() is None:
                logger.info(f"Flask server started successfully (PID: {self.server_process.pid})")
                self.restart_count = 0  # Reset restart counter on successful start
                return True
            else:
                logger.error("Flask server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Error starting Flask server: {e}")
            return False

    def stop_server(self):
        """Stop the Flask server process."""
        if self.server_process:
            try:
                logger.info(f"Stopping Flask server (PID: {self.server_process.pid})")
                
                # Try graceful shutdown first
                self.server_process.terminate()
                
                # Wait up to 10 seconds for graceful shutdown
                try:
                    self.server_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    logger.warning("Graceful shutdown failed, force killing process")
                    self.server_process.kill()
                    self.server_process.wait()
                
                logger.info("Flask server stopped")
                self.server_process = None
                
            except Exception as e:
                logger.error(f"Error stopping Flask server: {e}")

    def restart_server(self):
        """Restart the Flask server."""
        logger.info("Restarting Flask server...")
        
        # Stop current server
        self.stop_server()
        
        # Wait before restart
        time.sleep(self.restart_delay)
        
        # Start new server
        return self.start_server()

    def kill_existing_servers(self):
        """Kill any existing Flask/Python processes running on our port."""
        try:
            # Kill by process name
            subprocess.run(["taskkill", "/f", "/im", "python.exe"], 
                         capture_output=True, check=False)
            time.sleep(2)
            
            # Kill by port (if netstat shows processes on our port)
            result = subprocess.run(["netstat", "-ano"], 
                                  capture_output=True, text=True, check=False)
            
            for line in result.stdout.split('\n'):
                if ":25595" in line and "LISTENING" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        try:
                            subprocess.run(["taskkill", "/f", "/pid", pid], 
                                         capture_output=True, check=False)
                            logger.info(f"Killed process {pid} on port 25595")
                        except:
                            pass
                            
        except Exception as e:
            logger.warning(f"Error killing existing servers: {e}")

    def run(self):
        """Main watchdog loop."""
        logger.info("🐕 Flask Watchdog starting...")
        logger.info(f"Monitoring server at {self.server_url}")
        logger.info(f"Check interval: {self.check_interval} seconds")
        
        # Kill any existing servers first
        self.kill_existing_servers()
        
        # Start the server initially
        if not self.start_server():
            logger.error("Failed to start server initially, exiting")
            return
        
        # Main monitoring loop
        consecutive_failures = 0
        
        while self.running:
            try:
                # Check if server process is still running
                if self.server_process and self.server_process.poll() is not None:
                    logger.warning("Server process has died, restarting...")
                    if self.restart_server():
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                
                # Check server health
                elif not self.is_server_healthy():
                    consecutive_failures += 1
                    logger.warning(f"Server health check failed (attempt {consecutive_failures})")
                    
                    if consecutive_failures >= 3:  # Restart after 3 consecutive failures
                        logger.error("Multiple health check failures, restarting server...")
                        self.restart_count += 1
                        
                        if self.restart_count > self.max_restart_attempts:
                            logger.error(f"Max restart attempts ({self.max_restart_attempts}) reached, waiting longer...")
                            time.sleep(60)  # Wait 1 minute before trying again
                            self.restart_count = 0
                        
                        if self.restart_server():
                            consecutive_failures = 0
                        else:
                            logger.error("Failed to restart server")
                
                else:
                    # Server is healthy
                    if consecutive_failures > 0:
                        logger.info("Server recovered, health check passed")
                        consecutive_failures = 0
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in watchdog loop: {e}")
                time.sleep(self.check_interval)
        
        # Cleanup
        logger.info("Shutting down watchdog...")
        self.stop_server()
        logger.info("Watchdog shutdown complete")

if __name__ == "__main__":
    watchdog = FlaskWatchdog()
    watchdog.run()
