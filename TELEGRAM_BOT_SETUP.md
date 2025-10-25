# Telegram Bot Setup Guide for GramaFix

## 🎯 Why Telegram Bot?

✅ **100% FREE** - Unlimited messages, forever  
✅ **No Business Account** - Works with regular Telegram  
✅ **Instant Delivery** - Push notifications directly to user's phone  
✅ **Popular in India** - 700M+ users worldwide  
✅ **No SMS Costs** - Replace expensive SMS providers like Twilio  

---

## 📋 Prerequisites

- Telegram app installed on your phone
- Admin access to your GramaFix server
- 10-15 minutes for complete setup

---

## 🚀 Step 1: Create Your Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start a chat** with BotFather (official Telegram bot creator)
3. **Send command:** `/newbot`
4. **Choose a name** for your bot:
   - Example: `GramaFix Notifications`
   - This is the display name users will see
5. **Choose a username** for your bot:
   - Must end in `bot`
   - Example: `gramafix_bot` or `YourGramPanchayat_bot`
   - Must be unique across all Telegram bots
6. **Copy the Bot Token:**
   - BotFather will send you a token like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
   - Keep this secret! It's like a password for your bot

### Example Conversation with BotFather:

```
You: /newbot
BotFather: Alright, a new bot. How are we going to call it?
You: GramaFix Notifications
BotFather: Good. Now let's choose a username for your bot.
You: gramafix_bot
BotFather: Done! Congratulations on your new bot.
         Token: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
         Use this token to access the HTTP API.
```

---

## 🔧 Step 2: Configure Your Backend

### 2.1 Update `.env` File

Add these lines to your `Backend/.env` file:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_BOT_USERNAME=gramafix_bot
ENABLE_TELEGRAM_NOTIFICATIONS=true
```

**Replace:**
- `YOUR_BOT_TOKEN_HERE` with the token from BotFather
- `gramafix_bot` with your bot's username (without @)

### 2.2 Install Dependencies

```bash
cd Backend
pip install -r requirements.txt
```

This will install `python-telegram-bot>=20.7` and other required packages.

---

## 🌐 Step 3: Set Up Webhook (Production)

For production deployment, you need to tell Telegram where to send updates:

### 3.1 Get Your Server URL

- Example: `https://gramafix.yourdomain.com`
- Must be HTTPS (Telegram requires SSL)

### 3.2 Set Webhook

Run this command (replace with your values):

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://gramafix.yourdomain.com/api/telegram/webhook",
    "allowed_updates": ["message"]
  }'
```

**Or use this Python script:**

```python
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOUR_DOMAIN = "https://gramafix.yourdomain.com"  # Replace with your domain

async def setup_webhook():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            json={
                "url": f"{YOUR_DOMAIN}/api/telegram/webhook",
                "allowed_updates": ["message"]
            }
        )
        print(response.json())

import asyncio
asyncio.run(setup_webhook())
```

### 3.3 Verify Webhook

Check if webhook is set:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

You should see:
```json
{
  "ok": true,
  "result": {
    "url": "https://gramafix.yourdomain.com/api/telegram/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

---

## 🧪 Step 4: Test Your Bot

### 4.1 Restart Backend Server

```bash
cd Backend
python main.py
```

### 4.2 Test Connection Flow

1. **Login to GramaFix** as a regular user
2. **Go to Profile page** (will be updated with Telegram button)
3. **Click "Connect Telegram"** button
4. **You'll be redirected to Telegram** with your bot
5. **Bot sends /start command** automatically
6. **You should see:** "🎉 Successfully Connected!" message
7. **Go back to Profile** - should show "✅ Connected"

### 4.3 Test Notifications

1. **Report a new issue** on GramaFix
2. **Check Telegram** - you should receive:
   ```
   🆕 Issue Received!
   
   📋 Category: Roads
   📝 Description: Pothole on main road
   📍 Location: Your Gram Panchayat
   🆔 Issue ID: 12345
   ⏰ Status: Received
   ```

3. **Update issue status** (as admin/officer)
4. **Check Telegram** - you should receive:
   ```
   ⚙️ Issue Status Updated!
   
   🆔 Issue ID: 12345
   📋 Category: Roads
   
   🔄 Status Change:
      From: Received
      To: In Progress
   ```

---

## 🎨 Step 5: Customize Your Bot (Optional)

### 5.1 Set Bot Description

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setMyDescription" \
  -H "Content-Type: application/json" \
  -d '{"description": "Get instant notifications about your community issues from GramaFix"}'
```

### 5.2 Set Bot Commands

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setMyCommands" \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {"command": "start", "description": "Connect your GramaFix account"},
      {"command": "disconnect", "description": "Disconnect from GramaFix"}
    ]
  }'
```

### 5.3 Set Bot Profile Picture

1. Send a photo to @BotFather
2. Type `/setuserpic`
3. Select your bot
4. Send the photo you want to use

---

## 📱 How Users Connect Their Telegram

### For Citizens:

1. **Login to GramaFix**
2. **Click Profile** in navigation
3. **Click "Connect Telegram"** button
4. **Telegram app opens** automatically
5. **Click "START"** in Telegram chat
6. **Done!** They'll now receive instant notifications

### What Users See:

- **Before Connection:** "🔗 Connect Telegram" button
- **After Connection:** "✅ Telegram Connected" + "Disconnect" option
- **Notification Preview:** Shows when they'll receive messages

---

## 🛠️ Troubleshooting

### Bot Not Responding

**Check webhook status:**
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

**Look for errors:**
- `last_error_message`: Shows what went wrong
- `pending_update_count`: Should be 0 when working

**Common fixes:**
- Restart backend server
- Check TELEGRAM_BOT_TOKEN in .env
- Verify webhook URL is accessible (test with curl)
- Check backend logs for errors

### Users Not Receiving Notifications

**Verify user connection:**
```bash
# In MongoDB
db.users.findOne({ phone: "USER_PHONE" })
```

Should have:
- `telegram_chat_id`: "123456789"
- `telegram_connected_at`: timestamp

**Test sending manually:**
```python
from telegram_bot import send_telegram_message
import asyncio

async def test():
    result = await send_telegram_message(
        chat_id="USER_CHAT_ID",
        message="Test notification from GramaFix! 🎉"
    )
    print(f"Sent: {result}")

asyncio.run(test())
```

### Webhook Not Working (Local Development)

For **local testing**, use **ngrok** or similar:

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8000

# You'll get a URL like: https://abc123.ngrok.io
# Set webhook to this URL + /api/telegram/webhook
```

---

## 🔒 Security Best Practices

1. **Keep Bot Token Secret**
   - Never commit to git
   - Use environment variables
   - Rotate if exposed

2. **Validate Webhook Requests**
   - Current implementation accepts all updates
   - Add signature validation for production

3. **Rate Limiting**
   - Telegram allows 30 messages/second
   - We use background tasks to avoid blocking

4. **User Privacy**
   - Store only chat_id (anonymous identifier)
   - Allow users to disconnect anytime
   - Don't share user data

---

## 📊 Monitoring & Analytics

### Check Bot Statistics

**Total users connected:**
```javascript
// In MongoDB
db.users.countDocuments({ telegram_chat_id: { $exists: true } })
```

**Recent connections:**
```javascript
db.users.find(
  { telegram_chat_id: { $exists: true } },
  { name: 1, phone: 1, telegram_connected_at: 1 }
).sort({ telegram_connected_at: -1 }).limit(10)
```

### Monitor Notification Success

Add logging to `telegram_bot.py`:

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Will show:
# INFO: Telegram message sent successfully to 123456789
# ERROR: Failed to send Telegram message: 403 - Forbidden
```

---

## 💰 Cost Comparison

| Method | Cost per Message | Setup Complexity | Delivery Speed |
|--------|-----------------|------------------|----------------|
| **Telegram Bot** | **FREE** ✅ | Easy | Instant |
| Twilio SMS | $0.0079 | Medium | Fast |
| AWS SNS | $0.00645 | Hard | Fast |
| WhatsApp Business | Free (requires verification) | Very Hard | Instant |
| Email-to-SMS | Free (unreliable) | Easy | Slow |

**Telegram Bot is the clear winner!** 🏆

---

## 🎯 Next Steps

1. ✅ Complete Steps 1-4 above
2. ✅ Test with your own account
3. ✅ Update Profile.jsx to show Telegram connection UI
4. ✅ Announce to users: "Get instant updates via Telegram!"
5. ✅ Monitor connection rate and notifications

---

## 📞 Support

**Issues with setup?**
- Check backend logs: `tail -f backend.log`
- Test bot with BotFather's `/mybots` command
- Verify environment variables are loaded
- Check firewall allows HTTPS traffic

**Need help?**
- Telegram Bot API Docs: https://core.telegram.org/bots/api
- python-telegram-bot Docs: https://docs.python-telegram-bot.org/

---

## ✨ Features Included

✅ **Issue Created Notifications**
- Sent when user reports new issue
- Includes category, description, location

✅ **Status Update Notifications**
- Sent when admin/officer changes status
- Shows old → new status
- Custom emoji for each status

✅ **Easy Connection**
- One-click deep link
- Automatic account linking
- Disconnect option available

✅ **Rich Formatting**
- HTML formatting for readability
- Emoji for visual appeal
- Clean message layout

---

**Total Setup Time:** 15-30 minutes  
**Cost:** $0.00 forever  
**Maintenance:** Near zero  
**User Satisfaction:** 📈📈📈

Happy notifying! 🎉
