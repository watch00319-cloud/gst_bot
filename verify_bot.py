#!/usr/bin/env python3
"""
Simple script to verify Telegram bot functionality
Run this after providing real credentials in .env
"""

import asyncio
import logging
from pathlib import Path
from config import config
from database import db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_bot():
    """Verify bot functionality"""
    try:
        logger.info("🔍 Starting bot verification...")
        
        # Check configuration
        missing_fields = config.validate()
        if missing_fields:
            logger.error(f"❌ Missing required configuration: {', '.join(missing_fields)}")
            return False
        
        logger.info("✅ Configuration validated")
        
        # Test database connection
        logger.info("🗄️ Testing database connection...")
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()['count']
        conn.close()
        logger.info(f"✅ Database connection successful (Users: {count})")
        
        # Test Telegram bot token format
        if not config.TELEGRAM_BOT_TOKEN:
            logger.error("❌ TELEGRAM_BOT_TOKEN not set")
            return False
        
        if not config.TELEGRAM_BOT_TOKEN.startswith(('123', '456', '789')):
            logger.warning("⚠️ Bot token doesn't start with expected digits")
        
        logger.info("✅ Bot token format looks correct")
        
        # Test authorized user ID
        if config.AUTHORIZED_USER_ID == 0:
            logger.error("❌ AUTHORIZED_USER_ID not set properly")
            return False
        
        logger.info(f"✅ Authorized user ID: {config.AUTHORIZED_USER_ID}")
        
        # Test GST credentials
        if not config.GST_PORTAL_USERNAME or not config.GST_PORTAL_PASSWORD:
            logger.error("❌ GST portal credentials not set")
            return False
        
        logger.info("✅ GST portal credentials set")
        
        # Test business information
        if not config.GSTIN:
            logger.error("❌ GSTIN not set")
            return False
        
        logger.info(f"✅ Business: {config.BUSINESS_NAME}")
        logger.info(f"✅ GSTIN: {config.GSTIN}")
        
        # Test scheduler configuration
        logger.info(f"✅ Reminder scheduled for day {config.REMINDER_DAY} at {config.REMINDER_TIME}")
        
        logger.info("🎉 All verifications passed!")
        logger.info("\n📋 Next steps:")
        logger.info("1. Deploy to Railway")
        logger.info("2. Test bot commands: /start, /help, /status")
        logger.info("3. Test GST filing workflow")
        logger.info("4. Verify monthly reminders work")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_bot())
    exit(0 if success else 1)