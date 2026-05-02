"""
Telegram Bot module for GST Bot
Handles bot commands and user interactions
"""

import logging
from typing import Optional, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, ChatAction
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
from messages import get_text
import asyncio

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_ACTIVITY = 1
WAITING_FOR_OTP = 2
CONFIRMING_ACTION = 3

class GSTBot:
    """Professional Telegram GST Bot handler"""
    
    def __init__(self, token: str):
        """Initialize bot"""
        self.token = token
        self.app: Optional[Application] = None
        self.encryption_helper = EncryptionHelper(config.ENCRYPTION_KEY)
    
    def initialize(self) -> bool:
        """Initialize bot application"""
        try:
            self.app = Application.builder().token(self.token).build()
            self._setup_handlers()
            return True
        except Exception as e:
            logger.error(f"Error initializing bot: {e}", exc_info=True)
            return False
    
    def _setup_handlers(self) -> None:
        """Setup bot command and message handlers"""
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("admin", self.cmd_admin))
        
        # Main menu & common buttons
        self.app.add_handler(CallbackQueryHandler(self.btn_main_menu, pattern="^main_menu$"))
        self.app.add_handler(CallbackQueryHandler(self.btn_status, pattern="^gst_status$"))
        self.app.add_handler(CallbackQueryHandler(self.btn_file_gst, pattern="^file_gst$"))
        self.app.add_handler(CallbackQueryHandler(self.btn_history, pattern="^filing_history$"))
        self.app.add_handler(CallbackQueryHandler(self.btn_settings, pattern="^settings$"))
        self.app.add_handler(CallbackQueryHandler(self.btn_support, pattern="^support$"))
        
        # Settings handlers
        self.app.add_handler(CallbackQueryHandler(self.btn_toggle_reminders, pattern="^toggle_reminders$"))
        self.app.add_handler(CallbackQueryHandler(self.btn_toggle_auto_file, pattern="^toggle_auto_file$"))
        self.app.add_handler(CallbackQueryHandler(self.btn_change_language, pattern="^change_lang$"))
        self.app.add_handler(CallbackQueryHandler(self.set_language, pattern="^lang_"))
        
        # Admin handlers
        self.app.add_handler(CallbackQueryHandler(self.admin_stats, pattern="^admin_stats$"))
        
        self.app.add_error_handler(self.error_handler)

    async def check_auth(self, user_id: int) -> bool:
        """Check if user is authorized"""
        if user_id != config.AUTHORIZED_USER_ID:
            logger.warning(f"Unauthorized access attempt from user {user_id}")
            return False
        return True

    async def get_user_lang(self, telegram_id: int) -> str:
        """Get user's preferred language"""
        user = db.get_user(telegram_id)
        if user:
            settings = db.get_user_settings(user['user_id'])
            if settings:
                return settings.get('language', 'en')
        return 'en'

    def get_main_keyboard(self, lang: str) -> InlineKeyboardMarkup:
        """Generate main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton(get_text("btn_status", lang), callback_data="gst_status"),
                InlineKeyboardButton(get_text("btn_file", lang), callback_data="file_gst")
            ],
            [
                InlineKeyboardButton(get_text("btn_history", lang), callback_data="filing_history"),
                InlineKeyboardButton(get_text("btn_settings", lang), callback_data="settings")
            ],
            [
                InlineKeyboardButton(get_text("btn_support", lang), callback_data="support")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        user = update.effective_user
        if not await self.check_auth(user.id):
            await update.message.reply_text(get_text("unauthorized", "en"))
            return

        db.add_user(user.id, user.username, user.first_name, user.last_name)
        lang = await self.get_user_lang(user.id)
        
        await update.message.reply_text(
            get_text("welcome", lang),
            reply_markup=self.get_main_keyboard(lang),
            parse_mode=ParseMode.MARKDOWN
        )

    async def btn_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle main menu button"""
        query = update.callback_query
        await query.answer()
        lang = await self.get_user_lang(query.from_user.id)
        
        await query.edit_message_text(
            get_text("welcome", lang),
            reply_markup=self.get_main_keyboard(lang),
            parse_mode=ParseMode.MARKDOWN
        )

    async def btn_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show current GST status"""
        query = update.callback_query
        await query.answer()
        lang = await self.get_user_lang(query.from_user.id)
        
        status_text = f"{get_text('status_title', lang)}\n\n"
        status_text += f"🏢 *Business*: {config.BUSINESS_NAME}\n"
        status_text += f"🆔 *GSTIN*: `{config.GSTIN}`\n"
        status_text += f"📅 *Next Filing*: 20th {datetime.now().strftime('%B')}"
        
        keyboard = [[InlineKeyboardButton(get_text("btn_back", lang), callback_data="main_menu")]]
        await query.edit_message_text(status_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    async def btn_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle settings menu"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        lang = await self.get_user_lang(user_id)
        
        user_data = db.get_user(user_id)
        settings = db.get_user_settings(user_data['user_id'])
        
        rem_status = "✅ ON" if settings['reminder_enabled'] else "❌ OFF"
        auto_status = "✅ ON" if settings['auto_file_nil'] else "❌ OFF"
        
        settings_text = (
            f"{get_text('settings_title', lang)}\n\n"
            f"🔔 *Reminders*: {rem_status}\n"
            f"🤖 *Auto-File*: {auto_status}\n"
            f"🌐 *Language*: {lang.upper()}\n"
            f"📅 *Reminder Day*: {settings['reminder_day']}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton(f"🔔 Reminders: {rem_status}", callback_data="toggle_reminders")],
            [InlineKeyboardButton(f"🤖 Auto-File: {auto_status}", callback_data="toggle_auto_file")],
            [InlineKeyboardButton(get_text("btn_lang", lang), callback_data="change_lang")],
            [InlineKeyboardButton(get_text("btn_back", lang), callback_data="main_menu")]
        ]
        
        await query.edit_message_text(settings_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    async def btn_change_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Language selection menu"""
        query = update.callback_query
        await query.answer()
        lang = await self.get_user_lang(query.from_user.id)
        
        keyboard = [
            [InlineKeyboardButton("English 🇺🇸", callback_data="lang_en")],
            [InlineKeyboardButton("Hindi 🇮🇳", callback_data="lang_hi")],
            [InlineKeyboardButton(get_text("btn_back", lang), callback_data="settings")]
        ]
        await query.edit_message_text("🌐 *Select Language / भाषा चुनें*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    async def set_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Update language preference"""
        query = update.callback_query
        new_lang = query.data.split("_")[1]
        user_id = query.from_user.id
        
        user_data = db.get_user(user_id)
        db.update_user_settings(user_data['user_id'], language=new_lang)
        
        await query.answer(f"Language updated to {new_lang.upper()}")
        await self.btn_settings(update, context)

    async def btn_toggle_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Toggle reminder setting"""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        settings = db.get_user_settings(user_data['user_id'])
        
        new_val = not settings['reminder_enabled']
        db.update_user_settings(user_data['user_id'], reminder_enabled=new_val)
        
        await query.answer("Reminder status updated")
        await self.btn_settings(update, context)

    async def btn_toggle_auto_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Toggle auto-file setting"""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        settings = db.get_user_settings(user_data['user_id'])
        
        new_val = not settings['auto_file_nil']
        db.update_user_settings(user_data['user_id'], auto_file_nil=new_val)
        
        await query.answer("Auto-file status updated")
        await self.btn_settings(update, context)

    async def btn_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show support info"""
        query = update.callback_query
        await query.answer()
        lang = await self.get_user_lang(query.from_user.id)
        
        support_text = get_text("support_info", lang, business_name=config.BUSINESS_NAME, gstin=config.GSTIN)
        keyboard = [[InlineKeyboardButton(get_text("btn_back", lang), callback_data="main_menu")]]
        await query.edit_message_text(support_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    async def btn_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show filing history"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        lang = await self.get_user_lang(user_id)
        
        user_data = db.get_user(user_id)
        history = db.get_filing_history(user_data['user_id'], limit=5)
        
        history_text = f"{get_text('history_title', lang)}\n\n"
        if not history:
            history_text += get_text("no_history", lang)
        else:
            for f in history:
                icon = "✅" if f['status'] == 'success' else "⏳"
                history_text += f"{icon} *{f['month']} {f['year']}*: {f['status'].upper()}\n"
                if f['arn']: history_text += f"   └ ARN: `{f['arn']}`\n"
        
        keyboard = [[InlineKeyboardButton(get_text("btn_back", lang), callback_data="main_menu")]]
        await query.edit_message_text(history_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    async def btn_file_gst(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Initiate filing process"""
        query = update.callback_query
        await query.answer("Filing process starting...")
        await query.edit_message_text("🔄 *Starting Nil Return process...*\nPlease wait.", parse_mode=ParseMode.MARKDOWN)

    async def cmd_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Admin panel command"""
        if not await self.check_auth(update.effective_user.id):
            return
            
        lang = await self.get_user_lang(update.effective_user.id)
        keyboard = [
            [InlineKeyboardButton("📊 View Stats", callback_data="admin_stats")],
            [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
            [InlineKeyboardButton(get_text("btn_back", lang), callback_data="main_menu")]
        ]
        await update.message.reply_text(get_text("admin_panel", lang), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show admin stats"""
        query = update.callback_query
        await query.answer()
        
        conn = db.get_connection()
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        filing_count = conn.execute("SELECT COUNT(*) FROM gst_filings WHERE status='success'").fetchone()[0]
        conn.close()
        
        stats_text = (
            "📊 *System Statistics*\n\n"
            f"👥 *Total Users*: {user_count}\n"
            f"✅ *Successful Filings*: {filing_count}\n"
            f"⏱ *Uptime*: Active"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
        await query.edit_message_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors professionally"""
        logger.error(f"Update {update} caused error {context.error}")
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text("❌ *An error occurred.*\nPlease try again later or contact support.", parse_mode=ParseMode.MARKDOWN)

    def run(self) -> None:
        """Run the bot"""
        try:
            if not self.app:
                logger.error("Bot not initialized")
                return
            
            logger.info("Starting bot polling...")
            scheduler.start()
            self.app.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Error running bot: {e}", exc_info=True)
        finally:
            scheduler.stop()

    def stop(self) -> None:
        """Stop the bot"""
        scheduler.stop()
        logger.info("Bot stopped")

bot: Optional[GSTBot] = None

async def initialize_bot(token: str) -> bool:
    global bot
    bot = GSTBot(token)
    return bot.initialize()

def run_bot() -> None:
    global bot
    if bot: bot.run()

def stop_bot() -> None:
    global bot
    if bot: bot.stop()

async def send_reminder_message(user_id: int) -> None:
    """Send professional reminder message"""
    try:
        if not bot or not bot.app: return
        lang = await bot.get_user_lang(user_id)
        msg = "🔔 *GST Return Reminder*\n\nYour monthly filing is due. Please file your Nil return now." if lang == 'en' else "🔔 *GST रिटर्न रिमाइंडर*\n\nआपकी मासिक फाइलिंग बकाया है। कृपया अपना Nil रिटर्न अभी भरें।"
        keyboard = [[InlineKeyboardButton("📄 File Now", callback_data="file_gst")]]
        await bot.app.bot.send_message(chat_id=user_id, text=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error sending reminder: {e}")
