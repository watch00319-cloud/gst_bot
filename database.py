"""
Database module for GST Bot
Manages SQLite database for storing user data, GST filings, and history
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations"""
    
    def __init__(self, db_path: str = "gst_bot.db"):
        """Initialize database manager"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self) -> None:
        """Initialize database tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY NOT NULL,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone_number TEXT,
                    authorized BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # GST Filings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gst_filings (
                    filing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    month TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    filing_type TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    arn TEXT,
                    submission_date TIMESTAMP,
                    nil_return BOOLEAN DEFAULT 0,
                    has_activity BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, month, year)
                )
            """)
            
            # OTP Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS otp_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    filing_id INTEGER,
                    otp_token TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 3,
                    expire_time TIMESTAMP NOT NULL,
                    verified BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (filing_id) REFERENCES gst_filings(filing_id)
                )
            """)
            
            # User Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    reminder_enabled BOOLEAN DEFAULT 1,
                    reminder_day INTEGER DEFAULT 20,
                    reminder_time TEXT DEFAULT '09:00',
                    language TEXT DEFAULT 'en',
                    auto_file_nil BOOLEAN DEFAULT 0,
                    notification_enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Activity Log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            conn.commit()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            conn.close()
    
    # User operations
    def add_user(self, telegram_id: int, username: str = "", 
                 first_name: str = "", last_name: str = "") -> bool:
        """Add or update user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO users 
                (telegram_id, username, first_name, last_name, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (telegram_id, username, first_name, last_name))
            
            conn.commit()
            logger.info(f"User {telegram_id} added/updated")
            
            # Create default settings for new user
            cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
            if user:
                user_id = user['user_id']
                cursor.execute("""
                    INSERT OR IGNORE INTO user_settings (user_id)
                    VALUES (?)
                """, (user_id,))
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
        finally:
            conn.close()
    
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by telegram ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
            
            return dict(user) if user else None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
        finally:
            conn.close()
    
    # GST Filing operations
    def create_filing(self, user_id: int, month: str, year: int, 
                     filing_type: str = "nil") -> Optional[int]:
        """Create new GST filing record"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO gst_filings (user_id, month, year, filing_type, nil_return)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, month, year, filing_type, filing_type == "nil"))
            
            conn.commit()
            filing_id = cursor.lastrowid
            logger.info(f"Filing {filing_id} created for user {user_id}")
            
            return filing_id
        except Exception as e:
            logger.error(f"Error creating filing: {e}")
            return None
        finally:
            conn.close()
    
    def update_filing_status(self, filing_id: int, status: str, 
                            arn: Optional[str] = None) -> bool:
        """Update filing status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if arn:
                cursor.execute("""
                    UPDATE gst_filings 
                    SET status = ?, arn = ?, submission_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE filing_id = ?
                """, (status, arn, filing_id))
            else:
                cursor.execute("""
                    UPDATE gst_filings 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE filing_id = ?
                """, (status, filing_id))
            
            conn.commit()
            logger.info(f"Filing {filing_id} status updated to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating filing status: {e}")
            return False
        finally:
            conn.close()
    
    def get_filing_history(self, user_id: int, limit: int = 12) -> List[Dict[str, Any]]:
        """Get filing history for user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM gst_filings 
                WHERE user_id = ?
                ORDER BY year DESC, month DESC
                LIMIT ?
            """, (user_id, limit))
            
            filings = [dict(row) for row in cursor.fetchall()]
            return filings
        except Exception as e:
            logger.error(f"Error getting filing history: {e}")
            return []
        finally:
            conn.close()
    
    # OTP Session operations
    def create_otp_session(self, user_id: int, filing_id: int, 
                          otp_token: str, expire_time: datetime) -> Optional[int]:
        """Create OTP session"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO otp_sessions (user_id, filing_id, otp_token, expire_time)
                VALUES (?, ?, ?, ?)
            """, (user_id, filing_id, otp_token, expire_time))
            
            conn.commit()
            session_id = cursor.lastrowid
            logger.info(f"OTP session {session_id} created for user {user_id}")
            
            return session_id
        except Exception as e:
            logger.error(f"Error creating OTP session: {e}")
            return None
        finally:
            conn.close()
    
    def verify_otp_session(self, session_id: int) -> bool:
        """Mark OTP session as verified"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE otp_sessions 
                SET verified = 1
                WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
            logger.info(f"OTP session {session_id} verified")
            return True
        except Exception as e:
            logger.error(f"Error verifying OTP session: {e}")
            return False
        finally:
            conn.close()
    
    def get_active_otp_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get active OTP session for user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM otp_sessions 
                WHERE user_id = ? AND verified = 0 
                AND expire_time > CURRENT_TIMESTAMP
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            
            session = cursor.fetchone()
            return dict(session) if session else None
        except Exception as e:
            logger.error(f"Error getting OTP session: {e}")
            return None
        finally:
            conn.close()
    
    def increment_otp_attempts(self, session_id: int) -> bool:
        """Increment OTP attempt counter"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE otp_sessions 
                SET attempts = attempts + 1
                WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error incrementing OTP attempts: {e}")
            return False
        finally:
            conn.close()
    
    # Settings operations
    def get_user_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user settings"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
            settings = cursor.fetchone()
            
            return dict(settings) if settings else None
        except Exception as e:
            logger.error(f"Error getting user settings: {e}")
            return None
        finally:
            conn.close()
    
    def update_user_settings(self, user_id: int, **kwargs) -> bool:
        """Update user settings"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            allowed_fields = [
                'reminder_enabled', 'reminder_day', 'reminder_time',
                'language', 'auto_file_nil', 'notification_enabled'
            ]
            
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not updates:
                return True
            
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [user_id]
            
            cursor.execute(f"""
                UPDATE user_settings 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, values)
            
            conn.commit()
            logger.info(f"Settings updated for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating user settings: {e}")
            return False
        finally:
            conn.close()
    
    # Activity Log operations
    def log_activity(self, user_id: int, action: str, details: str = "", 
                    status: str = "success") -> bool:
        """Log user activity"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO activity_logs (user_id, action, details, status)
                VALUES (?, ?, ?, ?)
            """, (user_id, action, details, status))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            return False
        finally:
            conn.close()
    
    def get_activity_logs(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get activity logs for user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM activity_logs 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            logs = [dict(row) for row in cursor.fetchall()]
            return logs
        except Exception as e:
            logger.error(f"Error getting activity logs: {e}")
            return []
        finally:
            conn.close()


# Global database instance - will be updated in app.py with proper path
db = DatabaseManager()
