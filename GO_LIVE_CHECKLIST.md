# GST Bot - Final Go-Live Checklist

## 🚨 IMMEDIATELY BEFORE DEPLOYMENT

### 1. Environment Setup
- [ ] Copy `.env.production` to `.env`
- [ ] Fill in ALL real values in `.env`:
  - `TELEGRAM_BOT_TOKEN` (from @BotFather)
  - `AUTHORIZED_USER_ID` (from @userinfobot)
  - `GST_PORTAL_USERNAME` (real GST username)
  - `GST_PORTAL_PASSWORD` (real GST password)
  - `GSTIN` (real GST number)
  - `ENCRYPTION_KEY` (generate new key)

### 2. Configuration Verification
- [ ] Run `python verify_bot.py` - must pass all checks
- [ ] Verify Telegram bot token is valid (test with /start)
- [ ] Verify GST portal credentials work manually
- [ ] Check database path is `data/gst_bot.db`

### 3. Railway Setup
- [ ] Push code to GitHub repository
- [ Railway Dashboard ] Add all environment variables from `.env`
- [ Railway Dashboard ] Verify build settings:
  - Builder: Dockerfile
  - Start Command: `python app.py`
  - Healthcheck: `/health` (30s interval)

## 🚀 DEPLOYMENT COMMANDS

### Local Testing
```bash
# Test configuration
python verify_bot.py

# Test bot locally (optional)
python app.py
```

### Railway Deployment
```bash
# Commit and push
git add .
git commit -m "Final production deployment"
git push origin main

# Monitor deployment
# Check Railway dashboard for build status
```

## ✅ POST-DEPLOYMENT VERIFICATION

### Bot Functionality (within 5 minutes)
- [ ] Send `/start` to bot - must reply with welcome message
- [ ] Send `/help` - must show command list
- [ ] Send `/status` - must show filing status
- [ ] Verify only authorized user can access bot

### System Verification (within 15 minutes)
- [ ] Railway dashboard shows "Running" status
- [ ] Healthcheck passes (green checkmark)
- [ ] No restarts or crashes
- [ ] Memory usage < 500MB
- [ ] CPU usage < 50%

### Database Verification (within 30 minutes)
- [ ] Database file created in `data/` directory
- [ ] User registration works (test /start)
- [ ] Filing records can be created
- [ ] Logs show successful database operations

### Scheduler Verification (within 1 hour)
- [ ] Railway logs show scheduler started
- [ ] No scheduler errors in logs
- [ ] Next reminder scheduled correctly (day 20, 09:00 IST)

## 📊 MONITORING

### First 24 Hours
- [ ] Monitor Railway dashboard for issues
- [ ] Check bot responsiveness every 30 minutes
- [ ] Verify database file size grows appropriately
- [ ] Monitor memory/CPU usage

### Weekly Checks
- [ ] Verify monthly reminder triggers correctly
- [ ] Check filing success rate
- [ ] Review logs for errors
- [ ] Verify database backup strategy

## 🚨 CRITICAL SUCCESS INDICATORS

### Must-Have (Showstopper if failed)
1. **Bot responds to commands** - Telegram integration working
2. **Database creates files** - Data persistence working
3. **No crashes on startup** - Application stable
4. **Scheduler starts without errors** - Background tasks working

### Important (Should work)
1. **GST portal login** - Core functionality
2. **Monthly reminders** - Key feature
3. **Screenshot capture** - Filing confirmation
4. **OTP handling** - Authentication flow

## 🚨 IF DEPLOYMENT FAILS

### Quick Fixes
1. **Check Railway logs** - Look for specific error messages
2. **Verify environment variables** - All must be set in Railway dashboard
3. **Test bot token** - Must be valid and not expired
4. **Check database permissions** - Must be able to write to `data/` directory

### Common Issues
- **Bot token invalid** - Get new token from @BotFather
- **GST credentials wrong** - Test manual login first
- **Database path error** - Verify `data/` directory exists
- **Docker build fails** - Check Dockerfile syntax

## 🎯 GO-LIVE CONFIRMATION

### Final Checklist
- [ ] All environment variables set correctly
- [ ] Bot responds to all commands
- [ ] Database operations working
- [ ] Scheduler started successfully
- [ ] No errors in logs
- [ ] Railway dashboard shows healthy status

### Launch Authority
**✅ APPROVED FOR PRODUCTION DEPLOYMENT**

**Deployment Time:** [Fill in when ready]
**Contact Person:** [Fill in responsible person]
**Emergency Contact:** [Fill in contact info]

---

**Last Updated:** Final Go-Live Check
**Version:** 1.0.0 Production Ready

**Remember: Test thoroughly before going live!**