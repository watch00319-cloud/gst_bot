"""
GST Portal Login module
Handles authentication and navigation on GST portal using Playwright
"""

import logging
from typing import Optional, Tuple
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from config import config
import asyncio

logger = logging.getLogger(__name__)


class GSTPortalLogin:
    """Handles GST portal authentication and session management"""
    
    GST_PORTAL_URL = "https://www.gst.gov.in"
    GST_LOGIN_URL = "https://services.gst.gov.in/services/login"
    GSTR3B_URL = "https://services.gst.gov.in/services/gstrsearch?action=GSTR3B"
    
    def __init__(self):
        """Initialize GST Portal Login handler"""
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.username = config.GST_PORTAL_USERNAME
        self.password = config.GST_PORTAL_PASSWORD
    
    async def initialize_browser(self) -> bool:
        """
        Initialize Playwright browser
        
        Returns:
            True if successful, False otherwise
        """
        try:
            playwright = await async_playwright().start()
            
            browser_type = config.PLAYWRIGHT_BROWSER.lower()
            if browser_type == "chromium":
                self.browser = await playwright.chromium.launch(
                    headless=config.HEADLESS_MODE
                )
            elif browser_type == "firefox":
                self.browser = await playwright.firefox.launch(
                    headless=config.HEADLESS_MODE
                )
            else:
                self.browser = await playwright.webkit.launch(
                    headless=config.HEADLESS_MODE
                )
            
            logger.info(f"Browser initialized: {browser_type} (headless: {config.HEADLESS_MODE})")
            return True
        
        except Exception as e:
            logger.error(f"Error initializing browser: {e}")
            return False
    
    async def create_context(self) -> bool:
        """
        Create browser context
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.browser:
                return False
            
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            
            logger.info("Browser context created")
            return True
        
        except Exception as e:
            logger.error(f"Error creating browser context: {e}")
            return False
    
    async def login(self) -> Tuple[bool, str]:
        """
        Login to GST portal
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.page:
                return False, "Page not initialized"
            
            logger.info("Navigating to GST portal login page")
            await self.page.goto(self.GST_LOGIN_URL, wait_until="networkidle")
            
            # Wait for login form to load
            await self.page.wait_for_selector("input[type='text']", timeout=10000)
            
            # Enter username
            username_input = await self.page.query_selector("input[type='text']")
            if username_input:
                await username_input.fill(self.username)
                logger.info("Username entered")
            else:
                return False, "Username input field not found"
            
            # Enter password
            password_input = await self.page.query_selector("input[type='password']")
            if password_input:
                await password_input.fill(self.password)
                logger.info("Password entered")
            else:
                return False, "Password input field not found"
            
            # Click login button
            login_button = await self.page.query_selector("button[type='submit']")
            if login_button:
                await login_button.click()
                logger.info("Login button clicked")
            else:
                return False, "Login button not found"
            
            # Wait for navigation or OTP prompt
            try:
                await self.page.wait_for_url("**/dashboard**", timeout=15000)
                logger.info("Successfully logged in to GST portal")
                return True, "Logged in successfully"
            except:
                # Check if OTP is required
                otp_input = await self.page.query_selector("input[placeholder*='OTP']")
                if otp_input:
                    logger.info("OTP required for login")
                    return True, "OTP_REQUIRED"
                
                # Check for error message
                error_msg = await self.page.text_content(".alert-danger, .error-message")
                if error_msg:
                    logger.warning(f"Login error: {error_msg}")
                    return False, f"Login failed: {error_msg}"
                
                return False, "Login failed. Unexpected error."
        
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False, f"Error during login: {str(e)}"
    
    async def handle_otp(self, otp: str) -> Tuple[bool, str]:
        """
        Handle OTP verification during login
        
        Args:
            otp: OTP to submit
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.page:
                return False, "Page not initialized"
            
            logger.info("Entering OTP for login")
            
            # Find and fill OTP input
            otp_inputs = await self.page.query_selector_all("input[type='text']")
            if otp_inputs:
                for input_field in otp_inputs:
                    placeholder = await input_field.get_attribute("placeholder")
                    if placeholder and "OTP" in placeholder.upper():
                        await input_field.fill(otp)
                        logger.info("OTP entered")
                        break
            
            # Click submit/verify button
            verify_button = await self.page.query_selector("button[type='submit']")
            if verify_button:
                await verify_button.click()
                logger.info("OTP submitted")
            
            # Wait for dashboard navigation
            try:
                await self.page.wait_for_url("**/dashboard**", timeout=15000)
                logger.info("OTP verified, logged in successfully")
                return True, "OTP verified and logged in"
            except:
                error_msg = await self.page.text_content(".alert-danger, .error-message")
                if error_msg:
                    logger.warning(f"OTP verification error: {error_msg}")
                    return False, f"OTP verification failed: {error_msg}"
                
                return False, "OTP verification failed"
        
        except Exception as e:
            logger.error(f"Error during OTP handling: {e}")
            return False, f"Error during OTP handling: {str(e)}"
    
    async def navigate_to_gstr3b(self) -> Tuple[bool, str]:
        """
        Navigate to GSTR-3B filing page
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.page:
                return False, "Page not initialized"
            
            logger.info("Navigating to GSTR-3B page")
            await self.page.goto(self.GSTR3B_URL, wait_until="networkidle")
            
            # Wait for GSTR-3B form to load
            await self.page.wait_for_selector("select, button", timeout=10000)
            
            logger.info("GSTR-3B page loaded")
            return True, "GSTR-3B page loaded"
        
        except Exception as e:
            logger.error(f"Error navigating to GSTR-3B: {e}")
            return False, f"Error navigating to GSTR-3B: {str(e)}"
    
    async def select_nil_return(self, month: str, year: str) -> Tuple[bool, str]:
        """
        Select nil return option for given month/year
        
        Args:
            month: Month (e.g., "January")
            year: Year (e.g., "2024")
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.page:
                return False, "Page not initialized"
            
            logger.info(f"Selecting nil return for {month}/{year}")
            
            # Select month dropdown
            month_select = await self.page.query_selector("select[name='month']")
            if month_select:
                await month_select.select_option(month)
                logger.info(f"Month selected: {month}")
            
            # Select year dropdown
            year_select = await self.page.query_selector("select[name='year']")
            if year_select:
                await year_select.select_option(year)
                logger.info(f"Year selected: {year}")
            
            # Wait for form to update
            await self.page.wait_for_timeout(2000)
            
            # Check for nil return checkbox
            nil_checkbox = await self.page.query_selector("input[value='nil'], input[name*='nil']")
            if nil_checkbox:
                is_checked = await nil_checkbox.is_checked()
                if not is_checked:
                    await nil_checkbox.click()
                    logger.info("Nil return checkbox selected")
            
            return True, "Nil return selected"
        
        except Exception as e:
            logger.error(f"Error selecting nil return: {e}")
            return False, f"Error selecting nil return: {str(e)}"
    
    async def submit_nil_return(self) -> Tuple[bool, str]:
        """
        Submit nil return
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.page:
                return False, "Page not initialized"
            
            logger.info("Submitting nil return")
            
            # Find and click submit button
            submit_button = await self.page.query_selector("button[type='submit'], button:has-text('Submit')")
            if submit_button:
                await submit_button.click()
                logger.info("Submit button clicked")
            else:
                return False, "Submit button not found"
            
            # Wait for confirmation
            try:
                await self.page.wait_for_selector(".alert-success, .success-message, .confirmation", timeout=15000)
                success_msg = await self.page.text_content(".alert-success, .success-message, .confirmation")
                logger.info(f"Nil return submitted: {success_msg}")
                return True, "Nil return submitted successfully"
            except:
                return False, "Error confirming submission"
        
        except Exception as e:
            logger.error(f"Error submitting nil return: {e}")
            return False, f"Error submitting nil return: {str(e)}"
    
    async def take_screenshot(self, file_path: str) -> bool:
        """
        Take screenshot of current page
        
        Args:
            file_path: Path to save screenshot
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.page:
                return False
            
            await self.page.screenshot(path=file_path)
            logger.info(f"Screenshot saved: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return False
    
    async def close(self) -> None:
        """Close browser and context"""
        try:
            if self.page:
                await self.page.close()
            
            if self.context:
                await self.context.close()
            
            if self.browser:
                await self.browser.close()
            
            logger.info("Browser closed")
        
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize_browser()
        await self.create_context()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Helper function for complete login flow
async def perform_gst_login() -> Tuple[bool, GSTPortalLogin, str]:
    """
    Perform complete GST portal login
    
    Returns:
        Tuple of (success, portal_instance, message)
    """
    try:
        portal = GSTPortalLogin()
        
        # Initialize browser
        if not await portal.initialize_browser():
            return False, portal, "Failed to initialize browser"
        
        # Create context
        if not await portal.create_context():
            await portal.close()
            return False, portal, "Failed to create browser context"
        
        # Attempt login
        success, message = await portal.login()
        
        if not success:
            await portal.close()
            return False, portal, message
        
        if message == "OTP_REQUIRED":
            return True, portal, "OTP_REQUIRED"
        
        logger.info("GST portal login successful")
        return True, portal, "Login successful"
    
    except Exception as e:
        logger.error(f"Error in perform_gst_login: {e}")
        return False, None, f"Error: {str(e)}"
