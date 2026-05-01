"""
Configuration module for GST Bot
Handles environment variables and application settings
"""

import os
from dataclasses import dataclass
from typing import Optional
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Config:
    """Application configuration loaded from environment variables"""
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    AUTHORIZED_USER_ID: int = int(os.getenv("AUTHORIZED_USER_ID", "0"))
    
    # GST Portal Credentials (encrypted)
    GST_PORTAL_USERNAME: str = os.getenv("GST_PORTAL_USERNAME", "")
    GST_PORTAL_PASSWORD: str = os.getenv("GST_PORTAL_PASSWORD", "")
    
    # Railway Configuration
    RAILWAY_ENVIRONMENT: str = os.getenv("RAILWAY_ENVIRONMENT", "production")
    RAILWAY_STATIC_URL: str = os.getenv("RAILWAY_STATIC_URL", "")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///gst_bot.db")
    USE_SQLITE: bool = "sqlite" in DATABASE_URL.lower()
    
    # Scheduler Configuration
    REMINDER_DAY: int = int(os.getenv("REMINDER_DAY", "20"))  # Day of month to send reminder
    REMINDER_TIME: str = os.getenv("REMINDER_TIME", "09:00")  # Time to send reminder
    
    # Playwright Configuration
    HEADLESS_MODE: bool = os.getenv("HEADLESS_MODE", "true").lower() == "true"
    PLAYWRIGHT_BROWSER: str = os.getenv("PLAYWRIGHT_BROWSER", "chromium")
    
    # Security
    ENCRYPTION_KEY: Optional[bytes] = None
    
    # Gemini AI (optional)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    USE_AI: bool = bool(GEMINI_API_KEY)
    
    # Business Details
    BUSINESS_NAME: str = os.getenv("BUSINESS_NAME", "The Nutrition Hut")
    GSTIN: str = os.getenv("GSTIN", "")  # GST Identification Number
    
    def __post_init__(self):
        """Initialize encryption key"""
        key = os.getenv("ENCRYPTION_KEY")
        if key:
            self.ENCRYPTION_KEY = key.encode() if isinstance(key, str) else key
        else:
            # Generate a new key if not provided (for development)
            self.ENCRYPTION_KEY = Fernet.generate_key()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.RAILWAY_ENVIRONMENT == "production"
    
    def validate(self) -> list[str]:
        """Validate required configuration and return list of missing fields"""
        missing = []
        
        if not self.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        
        if self.AUTHORIZED_USER_ID == 0:
            missing.append("AUTHORIZED_USER_ID")
        
        if not self.GST_PORTAL_USERNAME:
            missing.append("GST_PORTAL_USERNAME")
        
        if not self.GST_PORTAL_PASSWORD:
            missing.append("GST_PORTAL_PASSWORD")
        
        return missing


class EncryptionHelper:
    """Helper class for encrypting/decrypting sensitive data"""
    
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive string data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted string data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()


# Global config instance
config = Config()
encryption = EncryptionHelper(config.ENCRYPTION_KEY) if config.ENCRYPTION_KEY else None


# Message templates in Hindi/Hinglish
MESSAGES = {
    "welcome": "Namaste! 🙏\n\nMain hoon The Nutrition Hut ka GST Bot.\nMain aapki monthly GST returns file karne mein madad karunga.\n\nUse /help to see all commands.",
    
    "help": """
📋 Available Commands:

/start - Bot shuru karein
/help - Yeh message dekhein
/status - Current GST filing status
/filegst - GST return file karein
/history - Purane filings dekhein
/settings - Bot settings badlein

📅 Monthly Process:
1. Due date se pehle reminder aayega
2. Poochhenge - kya sale/purchase hua?
3. Agar nil return hai toh OTP manga jayega
4. Return file ho jayega! 🎉
""",
    
    "gst_reminder": """
⚠️ GST Return Due Reminder!

Dear {business_name},

Aapki monthly GST return file karne ka time ho gaya hai!

Due date: {due_date}

Kya aapke is mahine mein koi transaction hua?
- No Activity (Nil Return)
- Sale
- Purchase
- Both

Reply karein ya button select karein.
""",
    
    "ask_activity": """
❓ Is mahine ( {month} ) kya activity hui?

Select karein:
""",
    
    "no_activity_confirm": """
👍 Toh aap keh rahe hain ki is mahine koi sale ya purchase nahi hua?

Main ab GST portal login karunga aur Nil Return file karunga.
""",
    
    "request_otp": """
🔐 GST Portal Login Successful!

Ab aapko OTP enter karna hoga.

GST portal par OTP aaya hoga. Woh OTP yahan bhejo.
""",
    
    "otp_received": """
✅ OTP receive ho gaya!

Verifying...
""",
    
    "nil_return_success": """
🎉 Badhai ho! 

Aapki GSTR-3B Nil Return successfully file ho gayi!

Filing Details:
- Month: {month}
- Type: Nil Return
- ARN: {arn}
- Date: {date}

Screenshot attached hai.
""",
    
    "nil_return_failed": """
❌ Kuch gadbad ho gayi!

Error: {error}

Kripya dubara try karein ya support se contact karein.
""",
    
    "already_filed": """
✅ Aapki GST return pehle se file ho chuki hai!

Filing Details:
- Month: {month}
- Type: {return_type}
- ARN: {arn}
- Date: {date}
""",
    
    "no_activity_recorded": """
📝 Activity Recorded: No Activity

Is mahine ki GST return file nahi hui.
""",
    
    "unauthorized": """
❌ Access Denied!

Aap is bot ka use nahi kar sakte.
Contact owner se.
""",
    
    "invalid_option": """
⚠️ Galat option!

Kripya sahi option select karein.
""",
    
    "processing": """
⏳ Processing...

Thoda wait karein...
""",
    
    "history_header": """
📜 GST Filing History:

""",
    
    "no_history": """
❌ Koi filing history nahi mili.
""",
    
    "settings": """
⚙️ Bot Settings:

Business Name: {business_name}
GSTIN: {gstin}
Reminder Day: {reminder_day} of each month
Current Status: {status}
""",
    
    "settings_updated": """
✅ Settings update ho gaye!
"""
}


def get_message(key: str, **kwargs) -> str:
    """Get formatted message from template"""
    template = MESSAGES.get(key, "Message not found")
    return template.format(**kwargs)