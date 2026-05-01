"""
Main application entry point for GST Bot
Initializes and runs the Telegram bot with Railway hosting support
"""

import logging
import asyncio
import sys
from pathlib import Path
from config import config
from database import db
from bot import initialize_bot, run_bot, stop_bot
from scheduler import scheduler

# Setup logging - reduced verbosity for production
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gst_bot.log')
    ]
)

logger = logging.getLogger(__name__)


async def validate_configuration() -> bool:
    """
    Validate required configuration
    
    Returns:
        True if valid, False otherwise
    """
    logger.warning("Validating configuration...")
    
    missing_fields = config.validate()
    
    if missing_fields:
        logger.error(f"Missing required configuration: {', '.join(missing_fields)}")
        return False
    
    logger.warning("✅ Configuration validated successfully")
    return True


async def setup_environment() -> bool:
    """
    Setup application environment
    
    Returns:
        True if successful
    """
    try:
        logger.warning("Setting up environment...")
        
        # Create necessary directories if not exists
        screenshots_dir = Path("screenshots")
        screenshots_dir.mkdir(exist_ok=True)
        logger.warning(f"Screenshots directory ready: {screenshots_dir}")
        
        # Create logs directory if not exists
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        logger.warning(f"Logs directory ready: {logs_dir}")
        
        # Ensure database directory exists and is writable
        db_dir = Path("data")
        db_dir.mkdir(exist_ok=True)
        logger.warning(f"Database directory ready: {db_dir}")
        
        # Update database path to use data directory for persistence
        from database import DatabaseManager
        db_manager = DatabaseManager("data/gst_bot.db")
        
        # Initialize database
        logger.warning("Initializing database...")
        db_manager.init_database()
        logger.warning("✅ Database initialized")
        
        # Test database connection
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()['count']
        conn.close()
        logger.warning(f"✅ Database connection test successful (Users: {count})")
        
        return True
    
    except Exception as e:
        logger.error(f"Error setting up environment: {e}")
        return False


def main() -> None:
    """Main application function"""
    try:
        # Validate configuration
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if not loop.run_until_complete(validate_configuration()):
            logger.error("Configuration validation failed")
            sys.exit(1)
        
        # Setup environment
        if not loop.run_until_complete(setup_environment()):
            logger.error("Environment setup failed")
            sys.exit(1)
            
        # Initialize bot
        bot_initialized = loop.run_until_complete(initialize_bot(config.TELEGRAM_BOT_TOKEN))
        if not bot_initialized:
            logger.error("Bot initialization failed")
            sys.exit(1)
        
        # Run bot (this will block until stopped)
        # We pass the loop to ensure run_polling uses the same one
        run_bot()
    
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
        stop_bot()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        stop_bot()
        sys.exit(1)
    finally:
        if 'loop' in locals() and loop.is_running():
            loop.stop()
        if 'loop' in locals() and not loop.is_closed():
            loop.close()


def main_sync() -> None:
    """Synchronous main function for entry point"""
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application stopped")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_sync()
