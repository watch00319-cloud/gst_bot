"""
Scheduler module for GST Bot
Manages scheduled tasks for reminders and maintenance
"""

import logging
from datetime import datetime, time
from typing import Optional, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import config
from database import db
import pytz

logger = logging.getLogger(__name__)


class GSTScheduler:
    """Manages scheduled tasks for GST reminders and maintenance"""
    
    def __init__(self):
        """Initialize scheduler"""
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.timezone = pytz.timezone('Asia/Kolkata')
        self.is_running = False
    
    def start(self) -> bool:
        """
        Start the scheduler
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.scheduler and self.scheduler.running:
                logger.info("Scheduler already running")
                return True
            
            self.scheduler = AsyncIOScheduler(timezone=self.timezone)
            
            # Parse reminder time (HH:MM format)
            reminder_time_parts = config.REMINDER_TIME.split(":")
            reminder_hour = int(reminder_time_parts[0])
            reminder_minute = int(reminder_time_parts[1]) if len(reminder_time_parts) > 1 else 0
            
            # Add job for sending reminders
            self.scheduler.add_job(
                self.send_monthly_reminder,
                CronTrigger(
                    day=config.REMINDER_DAY,
                    hour=reminder_hour,
                    minute=reminder_minute,
                    timezone=self.timezone
                ),
                id="send_reminder",
                name="Send monthly GST reminder",
                replace_existing=True
            )
            
            # Add job for cleaning up expired OTP sessions (daily)
            self.scheduler.add_job(
                self.cleanup_expired_otps,
                CronTrigger(hour=2, minute=0, timezone=self.timezone),  # 2 AM daily
                id="cleanup_otp",
                name="Clean expired OTP sessions",
                replace_existing=True
            )
            
            # Add job for checking filing deadlines (weekly)
            self.scheduler.add_job(
                self.check_filing_deadlines,
                CronTrigger(day_of_week=0, hour=8, minute=0, timezone=self.timezone),  # Sunday 8 AM
                id="check_deadlines",
                name="Check filing deadlines",
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            
            
            return True
        
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the scheduler"""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("Scheduler stopped")
        
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    async def send_monthly_reminder(self) -> None:
        """Send monthly GST reminder to authorized user"""
        try:
            logger.info("Sending monthly GST reminder")
            
            # Get authorized user
            from bot import send_reminder_message
            authorized_user_id = config.AUTHORIZED_USER_ID
            
            try:
                await send_reminder_message(authorized_user_id)
                logger.info(f"Reminder sent to user {authorized_user_id}")
                db.log_activity(authorized_user_id, "monthly_reminder_sent")
            
            except Exception as e:
                logger.error(f"Error sending reminder: {e}")
                db.log_activity(authorized_user_id, "monthly_reminder_failed", 
                               str(e), "error")
        
        except Exception as e:
            logger.error(f"Error in send_monthly_reminder: {e}")
    
    async def cleanup_expired_otps(self) -> None:
        """Clean up expired OTP sessions"""
        try:
            logger.info("Cleaning up expired OTP sessions")
            
            from otp_handler import otp_handler
            deleted_count = otp_handler.cleanup_expired_sessions()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired OTP sessions")
        
        except Exception as e:
            logger.error(f"Error cleaning up OTP sessions: {e}")
    
    async def check_filing_deadlines(self) -> None:
        """Check for upcoming filing deadlines"""
        try:
            logger.info("Checking filing deadlines")
            
            # Get all active users
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT user_id FROM users WHERE authorized = 1
            """)
            
            users = cursor.fetchall()
            conn.close()
            
            current_date = datetime.now()
            
            # Check for pending filings
            for user_row in users:
                user_id = user_row[0]
                filings = db.get_filing_history(user_id, limit=5)
                
                for filing in filings:
                    if filing['status'] == 'pending':
                        # Check if filing is overdue or due soon
                        filing_month = filing['month']
                        filing_year = filing['year']
                        
                        logger.info(f"Pending filing for user {user_id}: {filing_month}/{filing_year}")
        
        except Exception as e:
            logger.error(f"Error checking filing deadlines: {e}")
    
    def add_custom_job(self, func: Callable, job_id: str, name: str, 
                      trigger: CronTrigger, replace_existing: bool = True) -> bool:
        """
        Add custom scheduled job
        
        Args:
            func: Async function to execute
            job_id: Unique job ID
            name: Job name
            trigger: CronTrigger for job
            replace_existing: Replace if job exists
            
        Returns:
            True if successful
        """
        try:
            if not self.scheduler:
                logger.error("Scheduler not initialized")
                return False
            
            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                name=name,
                replace_existing=replace_existing
            )
            
            logger.info(f"Custom job added: {job_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding custom job: {e}")
            return False
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove scheduled job
        
        Args:
            job_id: Job ID to remove
            
        Returns:
            True if successful
        """
        try:
            if not self.scheduler:
                return False
            
            self.scheduler.remove_job(job_id)
            logger.info(f"Job removed: {job_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error removing job: {e}")
            return False
    
    def get_jobs(self) -> list:
        """
        Get all scheduled jobs
        
        Returns:
            List of scheduled jobs
        """
        try:
            if not self.scheduler:
                return []
            
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "trigger": str(job.trigger),
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None
                })
            
            return jobs
        
        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return []
    
    def pause_job(self, job_id: str) -> bool:
        """
        Pause a scheduled job
        
        Args:
            job_id: Job ID to pause
            
        Returns:
            True if successful
        """
        try:
            if not self.scheduler:
                return False
            
            self.scheduler.pause_job(job_id)
            logger.info(f"Job paused: {job_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error pausing job: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job
        
        Args:
            job_id: Job ID to resume
            
        Returns:
            True if successful
        """
        try:
            if not self.scheduler:
                return False
            
            self.scheduler.resume_job(job_id)
            logger.info(f"Job resumed: {job_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error resuming job: {e}")
            return False


# Global scheduler instance
scheduler = GSTScheduler()
