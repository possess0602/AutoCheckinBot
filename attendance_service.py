import schedule
import time
import logging
import signal
import sys
import os
import random
from datetime import datetime, timedelta
from manual_punch import punch_attendance, load_config
import threading

class AttendanceService:
    def __init__(self):
        self.running = True
        self.pid_file = 'attendance_service.pid'  # Windows compatible path
        self.punch_in_time = None  # Record punch-in time
        self.cookie_failure_count = 0  # Track consecutive cookie failures
        self.config = load_config()  # Load configuration
        self.setup_logging()
        self.setup_signal_handlers()
        self.write_pid()
    
    def setup_logging(self):
        """Setup logging - suitable for Linux environment"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('logs/attendance_service.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)  # Optional: display in foreground mode
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def write_pid(self):
        """Write PID file"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            self.logger.info(f"PID file created: {self.pid_file}")
        except Exception as e:
            self.logger.warning(f"Cannot create PID file: {e}")
    
    def remove_pid(self):
        """Remove PID file"""
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
                self.logger.info("PID file removed")
        except Exception as e:
            self.logger.warning(f"Cannot remove PID file: {e}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers - Linux standard signals"""
        signal.signal(signal.SIGINT, self.signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, self.signal_handler)  # Terminate signal
        if hasattr(signal, 'SIGHUP'):  # Linux reload signal
            signal.signal(signal.SIGHUP, self.reload_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, preparing to shutdown service...")
        self.running = False
    
    def reload_handler(self, signum, frame):
        """Handle reload signals"""
        self.logger.info("Received reload signal, reconfiguring schedule...")
        schedule.clear()
        self.setup_schedule()
    
    def generate_random_punch_times(self):
        """Generate random punch times using config settings"""
        work_schedule = self.config.get("work_schedule", {})
        
        # Get punch-in settings
        punch_in_config = work_schedule.get("punch_in", {})
        punch_in_hour = punch_in_config.get("hour", 9)
        punch_in_min_range = punch_in_config.get("minute_range", {})
        punch_in_min = punch_in_min_range.get("min", 10)
        punch_in_max = punch_in_min_range.get("max", 20)
        punch_in_minute = random.randint(punch_in_min, punch_in_max)
        
        # Get punch-out settings
        punch_out_config = work_schedule.get("punch_out", {})
        punch_out_hour = punch_out_config.get("hour", 18)
        punch_out_min_range = punch_out_config.get("minute_range", {})
        punch_out_min = punch_out_min_range.get("min", 10)
        punch_out_max = punch_out_min_range.get("max", 30)
        punch_out_minute = random.randint(punch_out_min, punch_out_max)
        
        punch_in_time = f"{punch_in_hour:02d}:{punch_in_minute:02d}"
        punch_out_time = f"{punch_out_hour:02d}:{punch_out_minute:02d}"
        
        return punch_in_time, punch_out_time
    
    def handle_cookie_failure(self, error_message: str):
        """Handle cookie failure scenarios"""
        self.cookie_failure_count += 1
        
        if "Cookie expired" in error_message or "refresh failed" in error_message:
            self.logger.error("[COOKIE] COOKIE EXPIRED - Manual intervention required!")
            self.logger.error("[ACTION] To fix this issue:")
            self.logger.error("   1. Run: python manual_punch.py update")
            self.logger.error("   2. Follow the guide to extract new cookies")
            self.logger.error("   3. Restart the service: ./stop_service.sh && ./start_service.sh")
            
            # Create alert file for external monitoring
            alert_file = "logs/cookie_alert.txt"
            with open(alert_file, 'w') as f:
                f.write(f"COOKIE EXPIRED at {datetime.now()}\n")
                f.write("Manual intervention required\n")
                f.write("Run: python manual_punch.py update\n")
        
        if self.cookie_failure_count >= 3:
            self.logger.warning("[WARNING] Multiple consecutive cookie failures detected")
            self.logger.warning("Service will continue running but manual cookie update is recommended")
    
    def handle_punch_success(self):
        """Reset failure count on successful punch"""
        if self.cookie_failure_count > 0:
            self.logger.info("[SUCCESS] Cookie issues resolved - resetting failure count")
            self.cookie_failure_count = 0
            
            # Remove alert file if it exists
            alert_file = "logs/cookie_alert.txt"
            if os.path.exists(alert_file):
                os.remove(alert_file)
    
    def punch_in(self):
        """Punch in for work"""
        self.logger.info("Starting punch-in process...")
        self.punch_in_time = datetime.now()
        
        try:
            result = punch_attendance(attendance_type=1)
            if result["success"]:
                self.logger.info(f"[SUCCESS] Punch-in successful! Time: {self.punch_in_time.strftime('%H:%M:%S')}")
                self.logger.info(f"Response: {result['data']}")
                self.handle_punch_success()
            else:
                error_msg = result.get('error', 'Unknown error')
                self.logger.error(f"[ERROR] Punch-in failed! Error: {error_msg}")
                self.handle_cookie_failure(error_msg)
        except Exception as e:
            self.logger.error(f"Punch-in exception: {str(e)}")
    
    def punch_out(self):
        """Punch out from work"""
        self.logger.info("Starting punch-out process...")
        punch_out_time = datetime.now()
        
        # Calculate work duration
        if self.punch_in_time:
            work_duration = punch_out_time - self.punch_in_time
            hours = work_duration.total_seconds() / 3600
            self.logger.info(f"Today's work duration: {hours:.2f} hours")
        
        try:
            result = punch_attendance(attendance_type=2)
            if result["success"]:
                self.logger.info(f"[SUCCESS] Punch-out successful! Time: {punch_out_time.strftime('%H:%M:%S')}")
                self.logger.info(f"Response: {result['data']}")
                self.handle_punch_success()
            else:
                error_msg = result.get('error', 'Unknown error')
                self.logger.error(f"[ERROR] Punch-out failed! Error: {error_msg}")
                self.handle_cookie_failure(error_msg)
        except Exception as e:
            self.logger.error(f"Punch-out exception: {str(e)}")
    
    def setup_schedule(self):
        """Setup random schedule using config settings"""
        schedule.clear()
        
        # Get workdays from config
        workdays = self.config.get("service_settings", {}).get("workdays", ["monday", "tuesday", "wednesday", "thursday", "friday"])
        
        # Generate random times for each workday
        for day in workdays:
            punch_in_time, punch_out_time = self.generate_random_punch_times()
            
            getattr(schedule.every(), day).at(punch_in_time).do(self.punch_in)
            getattr(schedule.every(), day).at(punch_out_time).do(self.punch_out)
            
            self.logger.info(f"{day.title()}: Punch-in {punch_in_time}, Punch-out {punch_out_time}")
        
        work_duration = self.config.get("work_schedule", {}).get("work_duration_hours", 9)
        self.logger.info(f"Random schedule setup completed (work duration: {work_duration} hours)")
    
    def run(self):
        """Main service loop"""
        self.logger.info(f"Attendance service started... (PID: {os.getpid()})")
        self.setup_schedule()
        
        try:
            check_interval = self.config.get("service_settings", {}).get("check_interval_seconds", 30)
            while self.running:
                schedule.run_pending()
                time.sleep(check_interval)  # Check interval from config
        except Exception as e:
            self.logger.error(f"Service runtime exception: {str(e)}")
        finally:
            self.remove_pid()
            self.logger.info("Attendance service stopped")

def main():
    # Check if instance is already running
    pid_file = 'attendance_service.pid'  # Windows compatible path
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            # Check if process is still running
            os.kill(old_pid, 0)
            print(f"Service already running (PID: {old_pid})")
            sys.exit(1)
        except (OSError, ValueError):
            # Process doesn't exist, remove old PID file
            os.remove(pid_file)
    
    service = AttendanceService()
    service.run()

if __name__ == "__main__":
    main() 