#!/usr/bin/env python3
"""
Background Service Manager for DBSBM Web Application
Manages both Flask service and Port 80 Proxy in the background
"""

import os
import sys
import time
import signal
import logging
import subprocess
import threading
from datetime import datetime
from pathlib import Path
import psutil
import json
from typing import Optional, Dict, Any

class ServiceManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.cgi_bin_dir = self.base_dir / "cgi-bin"
        self.log_dir = self.base_dir / "service_logs"
        self.pid_file = self.base_dir / "service_manager.pid"
        self.status_file = self.base_dir / "service_status.json"
        
        # Ensure directories exist
        self.log_dir.mkdir(exist_ok=True)
        
        # Service configuration
        self.services = {
            "flask": {
                "name": "Flask Web Service",
                "script": "flask_service.py",
                "working_dir": str(self.base_dir),
                "process": None,
                "pid": None,
                "status": "stopped",
                "restart_count": 0,
                "last_restart": None
            },
            "proxy": {
                "name": "Port 80 Proxy",
                "script": "port80_proxy.py",
                "working_dir": str(self.base_dir),
                "process": None,
                "pid": None,
                "status": "stopped",
                "restart_count": 0,
                "last_restart": None
            }
        }
        
        self.running = False
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(self.log_dir / f'service_manager_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ServiceManager')
        
    def write_pid_file(self):
        """Write current process PID to file"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            self.logger.info(f"PID file written: {self.pid_file}")
        except Exception as e:
            self.logger.error(f"Failed to write PID file: {e}")
            
    def remove_pid_file(self):
        """Remove PID file"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
                self.logger.info("PID file removed")
        except Exception as e:
            self.logger.error(f"Failed to remove PID file: {e}")
            
    def update_status(self):
        """Update service status file"""
        try:
            status_data = {
                "manager_pid": os.getpid(),
                "last_update": datetime.now().isoformat(),
                "services": {}
            }
            
            for service_name, service_info in self.services.items():
                status_data["services"][service_name] = {
                    "name": service_info["name"],
                    "status": service_info["status"],
                    "pid": service_info["pid"],
                    "restart_count": service_info["restart_count"],
                    "last_restart": service_info["last_restart"]
                }
                
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to update status file: {e}")
    
    def is_process_running(self, pid: int) -> bool:
        """Check if process with given PID is running"""
        try:
            return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
        except:
            return False
            
    def start_service(self, service_name: str) -> bool:
        """Start a specific service"""
        service = self.services[service_name]
        
        try:
            # Check if already running
            if service["pid"] and self.is_process_running(service["pid"]):
                self.logger.info(f"{service['name']} is already running (PID: {service['pid']})")
                service["status"] = "running"
                return True
                
            # Start the service
            script_path = Path(service["working_dir"]) / service["script"]
            
            if not script_path.exists():
                self.logger.error(f"Service script not found: {script_path}")
                service["status"] = "error"
                return False
                
            self.logger.info(f"Starting {service['name']}...")
            
            # Use CREATE_NEW_PROCESS_GROUP to allow proper signal handling
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=service["working_dir"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Give it a moment to start
            time.sleep(2)
            
            if process.poll() is None:  # Process is still running
                service["process"] = process
                service["pid"] = process.pid
                service["status"] = "running"
                service["restart_count"] += 1
                service["last_restart"] = datetime.now().isoformat()
                
                self.logger.info(f"{service['name']} started successfully (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                self.logger.error(f"{service['name']} failed to start:")
                self.logger.error(f"STDOUT: {stdout.decode()}")
                self.logger.error(f"STDERR: {stderr.decode()}")
                service["status"] = "error"
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start {service['name']}: {e}")
            service["status"] = "error"
            return False
            
    def stop_service(self, service_name: str) -> bool:
        """Stop a specific service"""
        service = self.services[service_name]
        
        try:
            if service["process"] and service["process"].poll() is None:
                self.logger.info(f"Stopping {service['name']} (PID: {service['pid']})...")
                
                if os.name == 'nt':
                    # Windows
                    service["process"].terminate()
                else:
                    # Unix/Linux
                    service["process"].send_signal(signal.SIGTERM)
                    
                # Wait for graceful shutdown
                try:
                    service["process"].wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Force killing {service['name']}")
                    service["process"].kill()
                    service["process"].wait()
                    
                service["process"] = None
                service["pid"] = None
                service["status"] = "stopped"
                self.logger.info(f"{service['name']} stopped successfully")
                return True
            else:
                self.logger.info(f"{service['name']} is not running")
                service["status"] = "stopped"
                service["pid"] = None
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to stop {service['name']}: {e}")
            return False
            
    def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        self.logger.info(f"Restarting {self.services[service_name]['name']}...")
        self.stop_service(service_name)
        time.sleep(2)
        return self.start_service(service_name)
        
    def check_service_health(self, service_name: str) -> bool:
        """Check if service is healthy"""
        service = self.services[service_name]
        
        if not service["pid"]:
            return False
            
        if not self.is_process_running(service["pid"]):
            self.logger.warning(f"{service['name']} process died (PID: {service['pid']})")
            service["status"] = "died"
            service["pid"] = None
            service["process"] = None
            return False
            
        service["status"] = "running"
        return True
        
    def monitor_services(self):
        """Monitor services and restart if needed"""
        while self.running:
            try:
                for service_name in self.services:
                    if not self.check_service_health(service_name):
                        if self.services[service_name]["status"] == "died":
                            self.logger.info(f"Restarting died service: {self.services[service_name]['name']}")
                            self.start_service(service_name)
                            
                self.update_status()
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error in service monitoring: {e}")
                time.sleep(30)
                
    def start_all_services(self):
        """Start all services"""
        self.logger.info("🚀 Starting DBSBM Background Service Manager")
        self.logger.info("=" * 60)
        
        success_count = 0
        for service_name in self.services:
            if self.start_service(service_name):
                success_count += 1
                
        self.logger.info(f"Started {success_count}/{len(self.services)} services")
        self.update_status()
        
        if success_count > 0:
            self.logger.info("🌐 Web services are now running in the background")
            self.logger.info("   - Flask App: http://localhost:5000")
            self.logger.info("   - Web Proxy: http://localhost")
            self.logger.info("=" * 60)
            
        return success_count == len(self.services)
        
    def stop_all_services(self):
        """Stop all services"""
        self.logger.info("Stopping all services...")
        
        for service_name in self.services:
            self.stop_service(service_name)
            
        self.update_status()
        self.logger.info("All services stopped")
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.stop_all_services()
        self.remove_pid_file()
        sys.exit(0)
        
    def run(self):
        """Main service manager loop"""
        try:
            # Setup signal handlers
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            self.write_pid_file()
            self.running = True
            
            # Start all services
            if not self.start_all_services():
                self.logger.error("Failed to start some services")
                return False
                
            # Start monitoring in background
            monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
            monitor_thread.start()
            
            self.logger.info("🔄 Service manager is now running. Press Ctrl+C to stop.")
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Service manager error: {e}")
        finally:
            self.stop_all_services()
            self.remove_pid_file()
            
    def status(self):
        """Show current service status"""
        print("\n" + "=" * 60)
        print("🔍 DBSBM Service Manager Status")
        print("=" * 60)
        
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    status_data = json.load(f)
                    
                print(f"Manager PID: {status_data.get('manager_pid', 'Unknown')}")
                print(f"Last Update: {status_data.get('last_update', 'Unknown')}")
                print("\nServices:")
                
                for service_name, service_info in status_data.get('services', {}).items():
                    status_icon = "🟢" if service_info['status'] == 'running' else "🔴"
                    print(f"  {status_icon} {service_info['name']}")
                    print(f"     Status: {service_info['status']}")
                    print(f"     PID: {service_info['pid'] or 'N/A'}")
                    print(f"     Restarts: {service_info['restart_count']}")
                    print(f"     Last Restart: {service_info['last_restart'] or 'Never'}")
                    print()
                    
            except Exception as e:
                print(f"Error reading status: {e}")
        else:
            print("No status file found. Service manager may not be running.")
            
        print("=" * 60)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python background_service_manager.py [start|stop|restart|status]")
        print("Commands:")
        print("  start   - Start service manager and all services")
        print("  stop    - Stop all services and service manager")
        print("  restart - Restart all services")
        print("  status  - Show current service status")
        sys.exit(1)
        
    command = sys.argv[1].lower()
    manager = ServiceManager()
    
    if command == "start":
        manager.run()
    elif command == "stop":
        manager.stop_all_services()
    elif command == "restart":
        manager.stop_all_services()
        time.sleep(2)
        manager.start_all_services()
    elif command == "status":
        manager.status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
