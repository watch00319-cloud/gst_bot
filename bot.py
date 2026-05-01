"""
Telegram Bot module for GST Bot
Handles bot commands and user interactions
"""

import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)
from datetime import datetime, timedelta
from config import config, EncryptionHelper
from database import db
from otp_handler import otp_handler
from nil_return import NilReturnWorkflow, get_or_create_workflow, cleanup_workflow
from scheduler import scheduler
import asyncio

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_ACTIVITY = 1
WAITING_FOR_OTP = 2
CONFIRMING_ACTION = 3

# Message templates
MESSAGES = {
    "start": """नमस्ते! 🙏
    
मैं GST Nil Return Bot हूँ, "The Nutrition Hut" के लिए।

मैं आपको monthly GST nil returns filing में मदद करता हूँ।

/help - सभी commands देखने के लिए
/status - current GST status
/filegst - GST nil return file करें
/settings - settings update करें""",
    
    "help": """📋 Available Commands:

/start - Bot को शुरू करें
/help - यह message
/status - GST filing status देखें
/filegst - Nil return file करें
/history - पिछली filings देखें
/settings - सेटिंग्स को configure करें

🔒 सभी data encrypted रहता है।
केवल authorized user ही access कर सकते हैं।""",
    
    "activity_prompt": """यह महीना क्या है - क्या कोई sale या purchase की activity है?""",
    
    "no_activity": """✅ कोई activity नहीं है।

अब Nil Return file करते हैं...
GST portal login हो रहे हैं...⏳""",
    
    "otp_prompt": """OTP भेजो जो GST portal से आया है।

(OTP 6-digit number है)
(Timeout: 10 minutes)""",
    
    "otp_verified": """✅ OTP verified!

Nil Return submit हो रहा है...⏳""",
    
    "success": """✅ Nil Return successfully file हो गई!

📄 Details:
• Month: {month}
• Year: {year}
• ARN: {arn}
• Submitted: {date}

Screenshot भी save हो गया है।""",
    
    "error": """❌ Error: {error}

कृपया फिर से try करें।""",
    
    "unauthorized": """🔒 Unauthorized Access

यह bot केवल authorized users के लिए है।
Administrator से contact करें।""",
}


class GSTBot:
    """Telegram GST Bot handler"""
    
    def __init__(self, token: str):
        """
        Initialize bot
        
        Args:
            token: Telegram bot token
        """
        self.token = token
        self.app: Optional[Application] = None
        self.encryption_helper = EncryptionHelper(config.ENCRYPTION_KEY)
    
    def initialize(self) -> bool:
        """
        Initialize bot application
        
        Returns:
            True if successful
        """
        try:
            self.app = Application.builder().token(self.token).build()
            
            # Add handlers
            self._setup_handlers()
            
            logger.info("Bot initialized successfully with handlers:")
            logger.info("  - Command handlers: start, help, status, filegst, history, settings")
            logger.info("  - Callback handlers: activity_no, activity_has, cancel")
            logger.info("  - Message handler: text input")
            logger.info("  - Error handler: global error handling")
            
            return True
        
        except Exception as e:
            logger.error(f"Error initializing bot: {e}", exc_info=True)
            return False
    
    def _setup_handlers(self) -> None:
        """Setup bot command and message handlers"""
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("filegst", self.cmd_filegst))
        self.app.add_handler(CommandHandler("history", self.cmd_history))
        self.app.add_handler(CommandHandler("settings", self.cmd_settings))
        
        # Callback handlers for buttons
        self.app.add_handler(CallbackQueryHandler(self.btn_no_activity, pattern="^activity_no$"))
        self.app.add_handler(CallbackQueryHandler(self.btn_has_activity, pattern="^activity_has$"))
        self.app.add_handler(CallbackQueryHandler(self.btn_cancel, pattern="^cancel$"))
        
        # Message handler for OTP input
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.msg_handle))
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
    
    async def check_auth(self, user_id: int) -> bool:
        """
        Check if user is authorized
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if authorized
        """
        if user_id != config.AUTHORIZED_USER_ID:
            logger.warning(f"Unauthorized access attempt from user {user_id}")
            return False
        
        return True
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        try:
            user = update.effective_user
            logger.info(f"/start command received from user {user.id} ({user.username or 'No username'})")
            
            if not await self.check_auth(user.id):
                logger.warning(f"Unauthorized /start attempt from user {user.id}")
                await update.message.reply_text(MESSAGES["unauthorized"])
                return
            
            # Add or update user in database
            db.add_user(
                telegram_id=user.id,
                username=user.username or "",
                first_name=user.first_name or "",
                last_name=user.last_name or ""
            )
            
            db.log_activity(user.id, "bot_start")
            
            await update.message.reply_text(MESSAGES["start"])
            logger.info(f"Bot started successfully by user {user.id}")
        
        except Exception as e:
            logger.error(f"Error in cmd_start: {e}", exc_info=True)
            await update.message.reply_text(f"{MESSAGES['error'].format(error=str(e))}")
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        try:
            user = update.effective_user
            logger.info(f"/help command received from user {user.id} ({user.username or 'No username'})")
            
            if not await self.check_auth(user.id):
                logger.warning(f"Unauthorized /help attempt from user {user.id}")
                await update.message.reply_text(MESSAGES["unauthorized"])
                return
            
            await update.message.reply_text(MESSAGES["help"])
            db.log_activity(user.id, "help_requested")
            logger.info(f"Help displayed to user {user.id}")
        
        except Exception as e:
            logger.error(f"Error in cmd_help: {e}", exc_info=True)
            await update.message.reply_text(f"{MESSAGES['error'].format(error=str(e))}")
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command"""
        try:
            if not await self.check_auth(update.effective_user.id):
                await update.message.reply_text(MESSAGES["unauthorized"])
                return
            
            await update.message.reply_chat_action(ChatAction.TYPING)
            
            user = db.get_user(update.effective_user.id)
            if not user:
                await update.message.reply_text("User not found. Please use /start first.")
                return
            
            user_id = user['user_id']
            filings = db.get_filing_history(user_id, limit=3)
            
            if not filings:
                status_msg = "📊 Status:\n\nअभी तक कोई GST filing नहीं है।"
            else:
                status_msg = "📊 Status:\n\n"
                for filing in filings:
                    status = filing['status']
                    emoji = "⏳" if status == "pending" else "✅" if status == "submitted" else "❌"
                    status_msg += f"{emoji} {filing['month']}/{filing['year']} - {status}\n"
            
            await update.message.reply_text(status_msg)
            db.log_activity(user_id, "status_checked")
        
        except Exception as e:
            logger.error(f"Error in cmd_status: {e}")
            await update.message.reply_text(f"{MESSAGES['error'].format(error=str(e))}")
    
    async def cmd_filegst(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /filegst command"""
        try:
            if not await self.check_auth(update.effective_user.id):
                await update.message.reply_text(MESSAGES["unauthorized"])
                return ConversationHandler.END
            
            user = db.get_user(update.effective_user.id)
            if not user:
                await update.message.reply_text("User not found. Please use /start first.")
                return ConversationHandler.END
            
            user_id = user['user_id']
            
            # Store workflow context
            current_month = datetime.now().month
            current_year = datetime.now().year
            context.user_data['user_id'] = user_id
            context.user_data['month'] = current_month
            context.user_data['year'] = current_year
            
            # Ask about activity
            keyboard = [
                [InlineKeyboardButton("❌ No Activity", callback_data="activity_no"),
                 InlineKeyboardButton("✅ Has Activity", callback_data="activity_has")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                MESSAGES["activity_prompt"],
                reply_markup=reply_markup
            )
            
            db.log_activity(user_id, "filegst_initiated")
            
            return WAITING_FOR_ACTIVITY
        
        except Exception as e:
            logger.error(f"Error in cmd_filegst: {e}")
            await update.message.reply_text(f"{MESSAGES['error'].format(error=str(e))}")
            return ConversationHandler.END
    
    async def btn_no_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle no activity button"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = context.user_data.get('user_id')
            month = context.user_data.get('month')
            year = context.user_data.get('year')
            
            await query.edit_message_text(MESSAGES["no_activity"])
            
            # Create filing record
            filing_id = db.create_filing(user_id, f"Month_{month}", year, "nil")
            if not filing_id:
                await query.message.reply_text("Error creating filing record.")
                db.log_activity(user_id, "filing_creation_failed", "", "error")
                return ConversationHandler.END
            
            context.user_data['filing_id'] = filing_id
            
            # Start nil return workflow
            workflow = await get_or_create_workflow(user_id, filing_id, f"Month_{month}", year)
            success, message = await workflow.start_workflow()
            
            if not success:
                await query.message.reply_text(f"{MESSAGES['error'].format(error=message)}")
                await cleanup_workflow(filing_id)
                return ConversationHandler.END
            
            if message.startswith("OTP_REQUIRED:"):
                otp_token = message.split(":")[-1]
                context.user_data['workflow'] = workflow
                context.user_data['otp_session_id'] = workflow.otp_session_id
                
                await query.message.reply_text(
                    f"✅ Portal login successful (OTP required)\n\n"
                    f"OTP: {otp_token}\n\n"
                    f"{MESSAGES['otp_prompt']}"
                )
                
                return WAITING_FOR_OTP
            
            # No OTP needed, proceed to filing
            return await self._proceed_with_filing(query, context)
        
        except Exception as e:
            logger.error(f"Error in btn_no_activity: {e}")
            await query.message.reply_text(f"{MESSAGES['error'].format(error=str(e))}")
            return ConversationHandler.END
    
    async def btn_has_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle has activity button"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = context.user_data.get('user_id')
            db.log_activity(user_id, "activity_reported")
            
            await query.edit_message_text(
                "✅ Activity noted.\n\n"
                "Detailed entry form coming soon! 🚧\n\n"
                "For now, please manually file your GST return."
            )
            
            return ConversationHandler.END
        
        except Exception as e:
            logger.error(f"Error in btn_has_activity: {e}")
            return ConversationHandler.END
    
    async def btn_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle cancel button"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = context.user_data.get('user_id')
            filing_id = context.user_data.get('filing_id')
            
            if filing_id:
                workflow = context.user_data.get('workflow')
                if workflow:
                    await workflow.cancel_workflow()
                    await cleanup_workflow(filing_id)
            
            await query.edit_message_text("❌ Operation cancelled.")
            
            if user_id:
                db.log_activity(user_id, "filing_cancelled")
            
            return ConversationHandler.END
        
        except Exception as e:
            logger.error(f"Error in btn_cancel: {e}")
            return ConversationHandler.END
    
    async def msg_handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle text messages"""
        try:
            user = update.effective_user
            message_text = update.message.text
            
            # Log all incoming messages
            logger.info(f"Message received from user {user.id} ({user.username or 'No username'}): {message_text}")
            
            if not await self.check_auth(user.id):
                logger.warning(f"Unauthorized message from user {user.id}")
                await update.message.reply_text(MESSAGES["unauthorized"])
                return ConversationHandler.END
            
            user_id = context.user_data.get('user_id')
            
            # Check if waiting for OTP
            if context._state.get("waiting_for") == WAITING_FOR_OTP or "workflow" in context.user_data:
                logger.info(f"OTP input received from user {user.id}")
                return await self._handle_otp_input(update, context)
            
            # Default response for non-command messages
            await update.message.reply_text("I don't understand that command. Use /help to see available commands.")
            return ConversationHandler.END
        
        except Exception as e:
            logger.error(f"Error in msg_handle: {e}", exc_info=True)
            await update.message.reply_text(f"{MESSAGES['error'].format(error=str(e))}")
            return ConversationHandler.END
    
    async def _handle_otp_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle OTP input from user"""
        try:
            otp = update.message.text.strip()
            user_id = context.user_data.get('user_id')
            workflow = context.user_data.get('workflow')
            
            if not workflow:
                await update.message.reply_text("Session expired. Please try /filegst again.")
                return ConversationHandler.END
            
            # Remove the OTP message for security
            try:
                await update.message.delete()
            except:
                pass
            
            await update.message.reply_text("OTP verify हो रहा है...⏳")
            
            # Submit OTP
            success, message = await workflow.submit_otp(otp)
            
            if not success:
                await update.message.reply_text(f"{MESSAGES['error'].format(error=message)}")
                return WAITING_FOR_OTP
            
            # Proceed with filing
            return await self._proceed_with_filing(update, context)
        
        except Exception as e:
            logger.error(f"Error in _handle_otp_input: {e}")
            await update.message.reply_text(f"{MESSAGES['error'].format(error=str(e))}")
            return ConversationHandler.END
    
    async def _proceed_with_filing(self, update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Proceed with nil return filing"""
        try:
            workflow = context.user_data.get('workflow')
            user_id = context.user_data.get('user_id')
            filing_id = context.user_data.get('filing_id')
            
            if not workflow:
                await update.message.reply_text("Session expired. Please try /filegst again.")
                return ConversationHandler.END
            
            await update.message.reply_text("Nil Return file हो रहा है...⏳")
            
            # File nil return
            success, message = await workflow.file_nil_return()
            
            if not success:
                await update.message.reply_text(f"{MESSAGES['error'].format(error=message)}")
                await cleanup_workflow(filing_id)
                return ConversationHandler.END
            
            # Success message
            success_msg = MESSAGES["success"].format(
                month=workflow.month,
                year=workflow.year,
                arn=workflow.arn,
                date=datetime.now().strftime("%d-%m-%Y %H:%M")
            )
            
            await update.message.reply_text(success_msg)
            
            # Cleanup
            await cleanup_workflow(filing_id)
            
            return ConversationHandler.END
        
        except Exception as e:
            logger.error(f"Error in _proceed_with_filing: {e}")
            await update.message.reply_text(f"{MESSAGES['error'].format(error=str(e))}")
            return ConversationHandler.END
    
    async def cmd_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /history command"""
        try:
            if not await self.check_auth(update.effective_user.id):
                await update.message.reply_text(MESSAGES["unauthorized"])
                return
            
            user = db.get_user(update.effective_user.id)
            if not user:
                await update.message.reply_text("User not found. Please use /start first.")
                return
            
            user_id = user['user_id']
            filings = db.get_filing_history(user_id, limit=12)
            
            if not filings:
                await update.message.reply_text("📋 History:\n\nकोई GST filing history नहीं है।")
                return
            
            history_msg = "📋 GST Filing History:\n\n"
            for idx, filing in enumerate(filings, 1):
                status_emoji = "✅" if filing['status'] == "submitted" else "❌" if filing['status'] == "failed" else "⏳"
                history_msg += (
                    f"{idx}. {filing['month']}/{filing['year']}\n"
                    f"   Status: {status_emoji} {filing['status']}\n"
                    f"   ARN: {filing['arn'] or '—'}\n\n"
                )
            
            await update.message.reply_text(history_msg)
            db.log_activity(user_id, "history_viewed")
        
        except Exception as e:
            logger.error(f"Error in cmd_history: {e}")
            await update.message.reply_text(f"{MESSAGES['error'].format(error=str(e))}")
    
    async def cmd_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /settings command"""
        try:
            if not await self.check_auth(update.effective_user.id):
                await update.message.reply_text(MESSAGES["unauthorized"])
                return
            
            user = db.get_user(update.effective_user.id)
            if not user:
                await update.message.reply_text("User not found. Please use /start first.")
                return
            
            user_id = user['user_id']
            settings = db.get_user_settings(user_id)
            
            if not settings:
                await update.message.reply_text("Settings not found.")
                return
            
            settings_msg = f"""⚙️ Settings:

📅 Reminder Day: {settings['reminder_day']}
⏰ Reminder Time: {settings['reminder_time']}
🔔 Notifications: {'✅ ON' if settings['notification_enabled'] else '❌ OFF'}
🤖 Auto-file Nil: {'✅ ON' if settings['auto_file_nil'] else '❌ OFF'}
🌐 Language: {settings['language']}

Settings update feature coming soon! 🚧"""
            
            await update.message.reply_text(settings_msg)
            db.log_activity(user_id, "settings_viewed")
        
        except Exception as e:
            logger.error(f"Error in cmd_settings: {e}")
            await update.message.reply_text(f"{MESSAGES['error'].format(error=str(e))}")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
    
    async def run(self) -> None:
        """Run the bot"""
        try:
            if not self.app:
                logger.error("Bot not initialized")
                return
            
            logger.info("Starting bot polling...")
            
            # Start scheduler in background
            scheduler.start()
            logger.info("Scheduler started successfully")
            
            # Start polling with error handling
            logger.info("Bot is running and waiting for updates...")
            await self.app.run_polling(drop_pending_updates=True)
        
        except Exception as e:
            logger.error(f"Error running bot: {e}", exc_info=True)
        
        finally:
            logger.info("Shutting down bot...")
            try:
                if self.app:
                    await self.app.stop()
                    logger.info("Bot stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping bot: {e}")
            finally:
                scheduler.stop()
                logger.info("Scheduler stopped")
    
    async def stop(self) -> None:
        """Stop the bot"""
        try:
            if self.app:
                await self.app.stop()
            
            scheduler.stop()
            logger.info("Bot stopped")
        
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")


# Global bot instance
bot: Optional[GSTBot] = None


async def initialize_bot(token: str) -> bool:
    """Initialize global bot instance"""
    global bot
    try:
        bot = GSTBot(token)
        return await bot.initialize()
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        return False


async def run_bot() -> None:
    """Run global bot instance"""
    global bot
    if bot:
        await bot.run()


async def stop_bot() -> None:
    """Stop global bot instance"""
    global bot
    if bot:
        await bot.stop()


async def send_reminder_message(user_id: int) -> None:
    """Send reminder message to user"""
    try:
        if not bot or not bot.app:
            logger.error("Bot not initialized")
            return
        
        message = (
            "🔔 GST Return Reminder\n\n"
            "यह महीने की GST return filing deadline आ गया है।\n\n"
            "अगर कोई sales/purchases नहीं है तो nil return file कर दो:\n\n"
            "/filegst - Nil return file करने के लिए"
        )
        
        await bot.app.bot.send_message(
            chat_id=user_id,
            text=message
        )
        
        logger.info(f"Reminder sent to user {user_id}")
    
    except Exception as e:
        logger.error(f"Error sending reminder: {e}")
