"""
OTP Handler module for GST Bot
Manages OTP handling, validation, and verification
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from database import db
import secrets
import hashlib

logger = logging.getLogger(__name__)


class OTPHandler:
    """Handles OTP generation and verification"""
    
    def __init__(self, otp_validity_minutes: int = 10):
        """
        Initialize OTP Handler
        
        Args:
            otp_validity_minutes: Time in minutes for OTP to remain valid
        """
        self.otp_validity_minutes = otp_validity_minutes
        self.otp_length = 6
    
    def generate_otp(self) -> str:
        """
        Generate a random 6-digit OTP
        
        Returns:
            6-digit OTP as string
        """
        return str(secrets.randbelow(1000000)).zfill(self.otp_length)
    
    def create_otp_session(self, user_id: int, filing_id: int) -> Tuple[bool, str, Optional[int]]:
        """
        Create new OTP session for user
        
        Args:
            user_id: User ID from database
            filing_id: GST filing ID
            
        Returns:
            Tuple of (success, token, session_id)
        """
        try:
            otp_token = self.generate_otp()
            expire_time = datetime.utcnow() + timedelta(minutes=self.otp_validity_minutes)
            
            session_id = db.create_otp_session(
                user_id=user_id,
                filing_id=filing_id,
                otp_token=otp_token,
                expire_time=expire_time
            )
            
            if session_id:
                logger.info(f"OTP session created for user {user_id}")
                return True, otp_token, session_id
            
            logger.error(f"Failed to create OTP session for user {user_id}")
            return False, "", None
        
        except Exception as e:
            logger.error(f"Error creating OTP session: {e}")
            return False, "", None
    
    def verify_otp(self, user_id: int, provided_otp: str) -> Tuple[bool, str, Optional[int]]:
        """
        Verify OTP provided by user
        
        Args:
            user_id: User ID from database
            provided_otp: OTP provided by user
            
        Returns:
            Tuple of (success, message, session_id)
        """
        try:
            # Get active OTP session
            session = db.get_active_otp_session(user_id)
            
            if not session:
                logger.warning(f"No active OTP session for user {user_id}")
                return False, "No active OTP session found. Please try again.", None
            
            session_id = session['session_id']
            
            # Check if OTP has expired
            expire_time = datetime.fromisoformat(session['expire_time'])
            if datetime.utcnow() > expire_time:
                logger.warning(f"OTP expired for session {session_id}")
                return False, "OTP has expired. Please request a new one.", session_id
            
            # Check attempt limit
            if session['attempts'] >= session['max_attempts']:
                logger.warning(f"Max OTP attempts exceeded for session {session_id}")
                return False, "Maximum OTP attempts exceeded. Please try again later.", session_id
            
            # Verify OTP
            if session['otp_token'] == provided_otp:
                # Mark session as verified
                if db.verify_otp_session(session_id):
                    logger.info(f"OTP verified successfully for user {user_id}")
                    return True, "OTP verified successfully!", session_id
                else:
                    logger.error(f"Failed to mark OTP session as verified: {session_id}")
                    return False, "Error verifying OTP. Please try again.", session_id
            
            # Increment attempts
            db.increment_otp_attempts(session_id)
            remaining_attempts = session['max_attempts'] - session['attempts'] - 1
            
            if remaining_attempts > 0:
                message = f"Invalid OTP. {remaining_attempts} attempts remaining."
            else:
                message = "Maximum OTP attempts exceeded. Please try again later."
            
            logger.warning(f"Invalid OTP attempt for session {session_id}")
            return False, message, session_id
        
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return False, "Error verifying OTP. Please try again.", None
    
    def get_session_status(self, session_id: int) -> dict:
        """
        Get OTP session status
        
        Args:
            session_id: OTP session ID
            
        Returns:
            Session status dictionary
        """
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM otp_sessions WHERE session_id = ?", (session_id,))
            session = cursor.fetchone()
            
            if session:
                session_dict = dict(session)
                expire_time = datetime.fromisoformat(session_dict['expire_time'])
                session_dict['is_expired'] = datetime.utcnow() > expire_time
                session_dict['remaining_attempts'] = session_dict['max_attempts'] - session_dict['attempts']
                return session_dict
            
            return {}
        
        except Exception as e:
            logger.error(f"Error getting session status: {e}")
            return {}
        
        finally:
            conn.close()
    
    def resend_otp(self, user_id: int, session_id: int) -> Tuple[bool, str]:
        """
        Resend OTP to user (generate new OTP)
        
        Args:
            user_id: User ID from database
            session_id: Previous session ID
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get current session details
            session = self.get_session_status(session_id)
            
            if not session:
                return False, "Session not found."
            
            if session['verified']:
                return False, "OTP already verified for this session."
            
            if session['is_expired']:
                return False, "Session expired. Please start fresh."
            
            # Generate new OTP for same session
            new_otp = self.generate_otp()
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Update session with new OTP
            new_expire_time = datetime.utcnow() + timedelta(minutes=self.otp_validity_minutes)
            cursor.execute("""
                UPDATE otp_sessions 
                SET otp_token = ?, attempts = 0, expire_time = ?
                WHERE session_id = ?
            """, (new_otp, new_expire_time, session_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"OTP resent for session {session_id}")
            return True, new_otp
        
        except Exception as e:
            logger.error(f"Error resending OTP: {e}")
            return False, "Error resending OTP. Please try again."
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired OTP sessions
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM otp_sessions 
                WHERE expire_time < CURRENT_TIMESTAMP
            """)
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired OTP sessions")
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"Error cleaning up OTP sessions: {e}")
            return 0


# Global OTP handler instance
otp_handler = OTPHandler()
