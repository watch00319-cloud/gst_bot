"""
Nil Return workflow module
Orchestrates the complete nil return filing process
"""

import logging
from typing import Optional, Tuple
from datetime import datetime
from enum import Enum
from gst_login import GSTPortalLogin, perform_gst_login
from otp_handler import otp_handler
from database import db
from config import config
import asyncio

logger = logging.getLogger(__name__)


class NilReturnStatus(Enum):
    """Enum for nil return workflow status"""
    INITIATED = "initiated"
    LOGIN_IN_PROGRESS = "login_in_progress"
    OTP_REQUIRED = "otp_required"
    OTP_VERIFIED = "otp_verified"
    FILING_IN_PROGRESS = "filing_in_progress"
    SUBMITTED = "submitted"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NilReturnWorkflow:
    """Manages the complete nil return filing workflow"""
    
    def __init__(self, user_id: int, filing_id: int, month: str, year: int):
        """
        Initialize nil return workflow
        
        Args:
            user_id: User ID from database
            filing_id: GST filing ID
            month: Month for filing (e.g., "April")
            year: Year for filing (e.g., 2024)
        """
        self.user_id = user_id
        self.filing_id = filing_id
        self.month = month
        self.year = year
        self.status = NilReturnStatus.INITIATED
        self.portal: Optional[GSTPortalLogin] = None
        self.otp_session_id: Optional[int] = None
        self.arn: Optional[str] = None
    
    async def start_workflow(self) -> Tuple[bool, str]:
        """
        Start the nil return workflow
        
        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info(f"Starting nil return workflow for user {self.user_id}, filing {self.filing_id}")
            
            # Update filing status
            db.update_filing_status(self.filing_id, "in_progress")
            db.log_activity(self.user_id, "nil_return_initiated", 
                           f"Month: {self.month}, Year: {self.year}")
            
            # Perform GST portal login
            self.status = NilReturnStatus.LOGIN_IN_PROGRESS
            success, portal, message = await perform_gst_login()
            
            if not success:
                logger.error(f"Login failed: {message}")
                self.status = NilReturnStatus.FAILED
                db.update_filing_status(self.filing_id, "failed", None)
                db.log_activity(self.user_id, "nil_return_login_failed", message, "error")
                return False, f"Login failed: {message}"
            
            self.portal = portal
            
            if message == "OTP_REQUIRED":
                logger.info("OTP required for login")
                self.status = NilReturnStatus.OTP_REQUIRED
                
                # Create OTP session
                success, otp_token, session_id = otp_handler.create_otp_session(
                    user_id=self.user_id,
                    filing_id=self.filing_id
                )
                
                if success and session_id:
                    self.otp_session_id = session_id
                    db.log_activity(self.user_id, "otp_session_created", 
                                   f"Session: {session_id}", "success")
                    return True, f"OTP_REQUIRED:{otp_token}"
                else:
                    self.status = NilReturnStatus.FAILED
                    await self.portal.close()
                    self.portal = None
                    db.update_filing_status(self.filing_id, "failed")
                    db.log_activity(self.user_id, "otp_creation_failed", 
                                   "Failed to create OTP session", "error")
                    return False, "Failed to create OTP session"
            
            logger.info("GST portal login successful")
            self.status = NilReturnStatus.OTP_VERIFIED
            db.log_activity(self.user_id, "gst_portal_login_success")
            return True, "login_success"
        
        except Exception as e:
            logger.error(f"Error starting workflow: {e}")
            self.status = NilReturnStatus.FAILED
            if self.portal:
                await self.portal.close()
            db.update_filing_status(self.filing_id, "failed")
            db.log_activity(self.user_id, "workflow_error", str(e), "error")
            return False, f"Workflow error: {str(e)}"
    
    async def submit_otp(self, otp: str) -> Tuple[bool, str]:
        """
        Submit OTP for login
        
        Args:
            otp: OTP provided by user
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.portal:
                return False, "Portal not initialized"
            
            if not self.otp_session_id:
                return False, "OTP session not found"
            
            logger.info(f"Verifying OTP for user {self.user_id}")
            
            # Verify OTP with handler
            success, message, session_id = otp_handler.verify_otp(self.user_id, otp)
            
            if not success:
                logger.warning(f"OTP verification failed: {message}")
                db.log_activity(self.user_id, "otp_verification_failed", message, "error")
                return False, message
            
            # Submit OTP to portal
            success, message = await self.portal.handle_otp(otp)
            
            if not success:
                logger.error(f"Portal OTP handling failed: {message}")
                self.status = NilReturnStatus.FAILED
                await self.portal.close()
                self.portal = None
                db.update_filing_status(self.filing_id, "failed")
                db.log_activity(self.user_id, "portal_otp_failed", message, "error")
                return False, message
            
            logger.info("OTP verified successfully")
            self.status = NilReturnStatus.OTP_VERIFIED
            db.log_activity(self.user_id, "otp_verified")
            return True, "OTP verified successfully"
        
        except Exception as e:
            logger.error(f"Error submitting OTP: {e}")
            self.status = NilReturnStatus.FAILED
            if self.portal:
                await self.portal.close()
            db.update_filing_status(self.filing_id, "failed")
            db.log_activity(self.user_id, "otp_submission_error", str(e), "error")
            return False, f"Error: {str(e)}"
    
    async def file_nil_return(self) -> Tuple[bool, str]:
        """
        File nil return after OTP verification
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.portal:
                return False, "Portal not initialized"
            
            if self.status != NilReturnStatus.OTP_VERIFIED:
                return False, f"Invalid status for filing: {self.status.value}"
            
            logger.info(f"Filing nil return for {self.month}/{self.year}")
            self.status = NilReturnStatus.FILING_IN_PROGRESS
            db.update_filing_status(self.filing_id, "filing_in_progress")
            
            # Navigate to GSTR-3B
            success, message = await self.portal.navigate_to_gstr3b()
            if not success:
                logger.error(f"Failed to navigate to GSTR-3B: {message}")
                self.status = NilReturnStatus.FAILED
                db.update_filing_status(self.filing_id, "failed")
                db.log_activity(self.user_id, "gstr3b_navigation_failed", message, "error")
                return False, message
            
            # Select nil return
            success, message = await self.portal.select_nil_return(self.month, str(self.year))
            if not success:
                logger.error(f"Failed to select nil return: {message}")
                self.status = NilReturnStatus.FAILED
                db.update_filing_status(self.filing_id, "failed")
                db.log_activity(self.user_id, "nil_return_selection_failed", message, "error")
                return False, message
            
            # Submit nil return
            success, message = await self.portal.submit_nil_return()
            if not success:
                logger.error(f"Failed to submit nil return: {message}")
                self.status = NilReturnStatus.FAILED
                db.update_filing_status(self.filing_id, "failed")
                db.log_activity(self.user_id, "nil_return_submission_failed", message, "error")
                return False, message
            
            # Take screenshot for confirmation
            screenshot_path = f"screenshots/nil_return_{self.filing_id}_{datetime.now().timestamp()}.png"
            await self.portal.take_screenshot(screenshot_path)
            
            logger.info("Nil return filed successfully")
            self.status = NilReturnStatus.SUBMITTED
            self.arn = f"ARN-{self.filing_id}"  # Placeholder ARN
            db.update_filing_status(self.filing_id, "submitted", self.arn)
            db.log_activity(self.user_id, "nil_return_submitted", 
                           f"ARN: {self.arn}, Screenshot: {screenshot_path}")
            
            return True, f"Nil return filed successfully! ARN: {self.arn}"
        
        except Exception as e:
            logger.error(f"Error filing nil return: {e}")
            self.status = NilReturnStatus.FAILED
            db.update_filing_status(self.filing_id, "failed")
            db.log_activity(self.user_id, "nil_return_error", str(e), "error")
            return False, f"Error: {str(e)}"
    
    async def cancel_workflow(self) -> bool:
        """
        Cancel the workflow
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Cancelling workflow for filing {self.filing_id}")
            self.status = NilReturnStatus.CANCELLED
            
            if self.portal:
                await self.portal.close()
                self.portal = None
            
            db.update_filing_status(self.filing_id, "cancelled")
            db.log_activity(self.user_id, "workflow_cancelled")
            
            return True
        
        except Exception as e:
            logger.error(f"Error cancelling workflow: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            if self.portal:
                await self.portal.close()
                self.portal = None
            
            logger.info(f"Workflow cleaned up for filing {self.filing_id}")
        
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_status(self) -> dict:
        """Get current workflow status"""
        return {
            "filing_id": self.filing_id,
            "user_id": self.user_id,
            "month": self.month,
            "year": self.year,
            "status": self.status.value,
            "arn": self.arn
        }


# Global workflow instance management
_active_workflows: dict[int, NilReturnWorkflow] = {}


async def get_or_create_workflow(user_id: int, filing_id: int, 
                                 month: str, year: int) -> NilReturnWorkflow:
    """
    Get or create a workflow instance
    
    Args:
        user_id: User ID from database
        filing_id: GST filing ID
        month: Month for filing
        year: Year for filing
    
    Returns:
        Workflow instance
    """
    if filing_id not in _active_workflows:
        _active_workflows[filing_id] = NilReturnWorkflow(user_id, filing_id, month, year)
    
    return _active_workflows[filing_id]


async def cleanup_workflow(filing_id: int) -> None:
    """Clean up workflow instance"""
    if filing_id in _active_workflows:
        await _active_workflows[filing_id].cleanup()
        del _active_workflows[filing_id]


def get_active_workflows() -> dict:
    """Get all active workflows"""
    return {
        fid: wf.get_status() 
        for fid, wf in _active_workflows.items()
    }
