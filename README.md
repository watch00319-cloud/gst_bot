# GST Nil Return Bot 🤖

A production-ready Telegram bot that automates monthly GST Nil Return filing for small businesses in India. Built for **The Nutrition Hut**.

## Features ✨

✅ **Telegram Bot Commands**
- `/start` - Initialize bot and register user
- `/help` - View all available commands
- `/status` - Check GST filing status
- `/filegst` - File monthly GST nil return
- `/history` - View filing history
- `/settings` - Configure bot settings

✅ **Automated Monthly Workflow**
- Monthly reminder before GST deadline
- Activity confirmation (Sale/Purchase/No Activity)
- Nil return filing for no-activity months

✅ **GST Portal Automation**
- Secure login with credential encryption
- OTP verification support
- Automated GSTR-3B nil return filing
- Screenshot capture for confirmation

✅ **Security Features**
- Only authorized Telegram user can access
- Credentials encrypted using Fernet
- Environment variables for secrets (no hardcoding)
- Activity logging for audit trail

✅ **Database Management**
- SQLite for simple file-based storage
- PostgreSQL support for production
- Complete filing history tracking
- OTP session management
- User settings persistence

✅ **Scheduler**
- Monthly reminders (configurable day & time)
- Automatic OTP cleanup
- Deadline checking

✅ **Production Ready**
- Railway.app deployment configuration
- Async/await for performance
- Comprehensive error handling
- Professional logging system
- Clean modular code architecture

## Tech Stack 🛠

- **Python 3.9+** - Core language
- **python-telegram-bot** - Telegram Bot API wrapper
- **Playwright** - Browser automation for GST portal
- **SQLite/PostgreSQL** - Database
- **APScheduler** - Task scheduling
- **Cryptography** - Data encryption
- **python-dotenv** - Environment management

## Project Structure 📁

```
gst_bot/
├── app.py                 # Main entry point
├── bot.py                 # Telegram bot logic
├── config.py              # Configuration & encryption
├── database.py            # SQLite database management
├── gst_login.py          # GST portal login automation
├── nil_return.py         # Nil return filing workflow
├── otp_handler.py        # OTP handling & verification
├── scheduler.py          # Background task scheduler
│
├── requirements.txt      # Python dependencies
├── Procfile             # Railway deployment
├── railway.json         # Railway configuration
├── .env.example         # Environment variables template
│
├── gst_bot.db           # SQLite database (auto-created)
├── screenshots/         # Filed return screenshots
├── logs/                # Application logs
└── README.md            # This file
```

## Installation 🚀

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Telegram account with @BotFather bot token
- GST Portal credentials

### Local Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd gst_bot
```

2. **Create virtual environment**
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install Playwright browsers**
```bash
playwright install chromium
```

5. **Create .env file**
```bash
cp .env.example .env
```

6. **Configure environment variables**
Edit `.env` with your values:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
AUTHORIZED_USER_ID=your_telegram_id
GST_PORTAL_USERNAME=your_gst_username
GST_PORTAL_PASSWORD=your_gst_password
GSTIN=your_gstin_number
BUSINESS_NAME=The Nutrition Hut
```

7. **Run the bot**
```bash
python app.py
```

## Environment Variables ⚙️

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram bot token from @BotFather | `123456:ABC...` |
| `AUTHORIZED_USER_ID` | ✅ | Your Telegram user ID | `123456789` |
| `GST_PORTAL_USERNAME` | ✅ | GST portal login username | `username@email.com` |
| `GST_PORTAL_PASSWORD` | ✅ | GST portal password (encrypted) | `password123` |
| `GSTIN` | ✅ | GST Identification Number | `27AABCT1234H1Z0` |
| `BUSINESS_NAME` | ❌ | Business name | `The Nutrition Hut` |
| `DATABASE_URL` | ❌ | Database connection string | `sqlite:///gst_bot.db` |
| `REMINDER_DAY` | ❌ | Day of month for reminder (1-31) | `20` |
| `REMINDER_TIME` | ❌ | Reminder time (HH:MM, 24-hour) | `09:00` |
| `HEADLESS_MODE` | ❌ | Run browser in headless mode | `true` |
| `PLAYWRIGHT_BROWSER` | ❌ | Browser engine to use | `chromium` |
| `ENCRYPTION_KEY` | ❌ | Fernet encryption key | Auto-generated |

## Database Schema 🗄️

### Tables
- `users` - Telegram users
- `gst_filings` - GST filing records
- `otp_sessions` - OTP verification sessions
- `user_settings` - User preferences
- `activity_logs` - Audit trail

## Usage Guide 📖

### Step 1: Start the Bot
```
/start
```
Bot will greet you and register your account.

### Step 2: File a Nil Return
```
/filegst
```
Bot will ask: "Is there any sale or purchase this month?"

### Step 3: Select Activity Status
Choose one of:
- ❌ **No Activity** - For nil return filing
- ✅ **Has Activity** - For detailed entry (coming soon)

### Step 4: OTP Verification
If no activity is selected:
1. Bot logs into GST portal
2. Bot requests OTP from portal
3. Send the 6-digit OTP to bot
4. Bot verifies and files nil return

### Step 5: Confirmation
Bot sends success message with:
- ARN (Acknowledgment Reference Number)
- Filing date/time
- Screenshot of confirmation

## Deployment on Railway 🚂

### Prerequisites
- Railway.app account (free tier available)
- GitHub repository with this code

### Steps

1. **Connect GitHub Repository**
   - Go to railway.app
   - Click "New Project" → "Deploy from GitHub"
   - Authorize & select `gst_bot` repository

2. **Add Environment Variables**
   - Go to project settings
   - Add all variables from `.env.example`
   - Click "Deploy"

3. **Railway Configuration**
   - `Procfile` - Entry point: `web: python app.py`
   - `railway.json` - Deployment configuration
   - Automatic restarts on failure

4. **Access Bot**
   - Bot will run 24/7 on Railway servers
   - Monthly reminders will be sent automatically
   - Check logs in Railway dashboard

### Railway Pricing
- Free tier includes: 500 hours/month (sufficient for 24/7 bot)
- Plus tier: $5/month for extra resources

## Security Considerations 🔒

1. **Environment Variables**
   - Never commit `.env` file
   - Use `.env.example` as template
   - Rotate credentials periodically

2. **Data Encryption**
   - GST credentials encrypted using Fernet
   - OTP tokens stored securely
   - Activity logs for audit trail

3. **Access Control**
   - Only authorized user can access bot
   - User ID validation on every command
   - Unauthorized access is logged

4. **Database Security**
   - SQLite file stored securely
   - PostgreSQL for production environments
   - Regular backups recommended

## Logging 📝

Logs are saved to:
- **Console** - Real-time output
- **File** - `gst_bot.log` - Persistent storage

Check logs in Railway dashboard (Production) or local file (Development).

## Troubleshooting 🔧

### Bot not responding?
- Check `TELEGRAM_BOT_TOKEN` is correct
- Ensure bot is running: `python app.py`
- Check logs for errors

### GST portal login fails?
- Verify `GST_PORTAL_USERNAME` and `GST_PORTAL_PASSWORD`
- GST portal might be down (check gst.gov.in)
- Try manual login first

### OTP not received?
- OTP expires after 10 minutes
- Request new OTP by starting `/filegst` again
- Check GST portal for OTP

### Database errors?
- Delete `gst_bot.db` and restart (will recreate)
- Check file permissions on database file
- Ensure write access to directory

## Future Features 🚀

- [ ] Sales invoice automation
- [ ] Purchase invoice tracking
- [ ] Detailed GSTR-3B filing with amounts
- [ ] Multi-user support
- [ ] Admin dashboard
- [ ] Email notifications
- [ ] WhatsApp integration
- [ ] AI-powered invoice analysis

## Support & Contribution 💬

For issues, questions, or contributions:
- Create GitHub issue
- Contact developer
- Email: support@example.com

## License 📄

This project is proprietary and confidential.
Developed for The Nutrition Hut.

## Credits 👏

- Built with ❤️ using Python
- Powered by Telegram Bot API
- Hosted on Railway.app
- GST automation using Playwright

---

**Made with ❤️ for automated GST compliance**

Last Updated: April 2026
Version: 1.0.0
