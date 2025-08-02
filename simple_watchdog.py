#!/usr/bin/env python3
"""
Simple Flask Server Watchdog - Keeps Flask server running
"""
import os
import sys
import time
import subprocess
import requests
import logging

# Simple logging setup without emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] Watchdog: %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleWatchdog:
    def __init__(self):
        self.server_process = None
        self.server_script = "c:\\Users\\Administrator\\Desktop\\DBSBMWEB\\cgi-bin\\production_server.py"
        self.python_exe = "C:/Users/Administrator/Desktop/DBSBMWEB/.venv/Scripts/python.exe"
        self.server_url = "http://localhost:25595/health"
        self.check_interval = 15  # Check every 15 seconds
        self.running = True

    def is_server_healthy(self):
        """Check if server is responding"""
        try:
            response = requests.get(self.server_url, timeout=3)
            return response.status_code == 200
        except:
            return False

    def start_server(self):
        """Start the Flask server"""
        try:
            logger.info("Starting Flask server...")
            
            cwd = "c:\\Users\\Administrator\\Desktop\\DBSBMWEB\\cgi-bin"
            
            self.server_process = subprocess.Popen(
                [self.python_exe, self.server_script],
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            time.sleep(5)  # Wait for server to start
            
            if self.server_process.poll() is None:
                logger.info(f"Server started (PID: {self.server_process.pid})")
                return True
            else:
                logger.error("Server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False

    def kill_existing_servers(self):
        """Kill any existing servers"""
        try:
            subprocess.run(["taskkill", "/f", "/im", "python.exe"], 
                         capture_output=True, check=False)
            time.sleep(2)
        except:
            pass

    def run(self):
        """Main watchdog loop"""
        logger.info("Flask Watchdog starting...")
        
        # Kill existing servers
        self.kill_existing_servers()
        
        # Start server
        if not self.start_server():
            logger.error("Failed to start server")
            return
        
        # Monitor loop
        while self.running:
            try:
                # Check if process died
                if self.server_process and self.server_process.poll() is not None:
                    logger.warning("Server process died, restarting...")
                    if not self.start_server():
                        logger.error("Failed to restart server")
                        time.sleep(30)
                
                # Check health
                elif not self.is_server_healthy():
                    logger.warning("Health check failed, restarting...")
                    self.kill_existing_servers()
                    if not self.start_server():
                        logger.error("Failed to restart server")
                        time.sleep(30)
                
                else:
                    logger.info("Server is healthy")
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping watchdog...")
                break
            except Exception as e:
                logger.error(f"Error in watchdog: {e}")
                time.sleep(self.check_interval)
        
        # Cleanup
        if self.server_process:
            try:
                self.server_process.terminate()
            except:
                pass

if __name__ == "__main__":
    watchdog = SimpleWatchdog()
    watchdog.run()
