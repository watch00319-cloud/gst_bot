# GST Bot Production Deployment Checklist

## 🚨 BEFORE DEPLOYMENT

### Environment Variables
- [ ] Replace `.env` with real values from `.env.production`
- [ ] Set all variables in Railway dashboard:
  - `TELEGRAM_BOT_TOKEN`
  - `AUTHORIZED_USER_ID`
  - `GST_PORTAL_USERNAME`
  - `GST_PORTAL_PASSWORD`
  - `GSTIN`
  - `ENCRYPTION_KEY`
- [ ] Verify Telegram bot token is valid
- [ ] Test Telegram bot responds to commands

### Database & Persistence
- [ ] Database path updated to `data/gst_bot.db`
- [ ] `data/` directory will be created on startup
- [ ] SQLite file will persist across Railway restarts

### Docker & Dependencies
- [ ] Dockerfile updated with Playwright browser installation
- [ ] All dependencies in `requirements.txt` are version-pinned
- [ ] Chromium browser installed in Docker image

### Configuration
- [ ] `railway.json` has production settings
- [ ] Healthcheck configured for Railway
- [ ] Environment variables optimized for production

## 🚀 DEPLOYMENT STEPS

1. **Commit Changes**
   ```bash
   git add .
   git commit -m "Production deployment preparation"
   git push origin main
   ```

2. **Deploy to Railway**
   - Railway should automatically detect the changes
   - Monitor build progress in Railway dashboard

3. **Verify Deployment**
   - Check Railway logs for startup errors
   - Verify bot is running and responding
   - Test database connection

## ✅ POST-DEPLOYMENT VERIFICATION

### Bot Functionality
- [ ] Send `/start` to bot - should respond with welcome message
- [ ] Send `/help` - should show command list
- [ ] Send `/status` - should show filing status
- [ ] Verify only authorized user can access bot

### Scheduler Testing
- [ ] Check scheduler jobs are running (Railway logs)
- [ ] Verify timezone is set to Asia/Kolkata
- [ ] Test monthly reminder trigger (set to day 20, 09:00)

### Database Operations
- [ ] Verify database file created in `data/` directory
- [ ] Check tables are created properly
- [ ] Test user registration and filing creation

### GST Portal Integration
- [ ] Test manual GST portal login flow
- [ ] Verify OTP handling works
- [ ] Test screenshot functionality

## 🔍 MONITORING

### Railway Dashboard
- [ ] Monitor CPU and memory usage
- [ ] Check application logs for errors
- [ ] Verify healthcheck passes
- [ ] Monitor restart patterns

### Application Logs
- [ ] Check `gst_bot.log` for errors
- [ ] Monitor database connection status
- [ ] Watch for Telegram API errors

## 🚨 CRITICAL SUCCESS FACTORS

1. **Telegram Bot Token** - Must be valid and bot must be accessible
2. **GST Portal Credentials** - Must be correct and account must be active
3. **Database Persistence** - SQLite file must survive restarts
4. **Browser Automation** - Playwright must work on Railway infrastructure
5. **Scheduler Timing** - Must trigger at correct Indian time

## 📞 SUPPORT

If deployment fails:
1. Check Railway logs for specific error messages
2. Verify all environment variables are set correctly
3. Test components locally before redeploying
4. Check Railway service status for any ongoing issues

## 🔄 MAINTENANCE

### Monthly Tasks
- [ ] Review filing success rate
- [ ] Check database size and performance
- [ ] Verify reminder system working
- [ ] Update GST credentials if changed

### Security
- [ ] Rotate encryption key periodically
- [ ] Update Telegram bot token if needed
- [ ] Monitor for unauthorized access attempts

---

**Last Updated:** Deployment Preparation
**Version:** 1.0.0 Production