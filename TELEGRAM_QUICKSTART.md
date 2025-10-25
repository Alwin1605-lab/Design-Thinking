# 🚀 Quick Start: Telegram Bot Integration

## ✅ What's Been Implemented

All the code for Telegram Bot notifications is **already implemented**! Here's what's ready:

### Backend (✅ Complete)
- ✅ `telegram_bot.py` - Helper module with notification functions
- ✅ Telegram webhook endpoint (`/api/telegram/webhook`)
- ✅ User connection endpoints (`/api/telegram/link`, `/api/telegram/status`, `/api/telegram/disconnect`)
- ✅ Auto-send notifications on issue creation
- ✅ Auto-send notifications on status updates
- ✅ Dependencies installed (`python-telegram-bot>=20.7`)

### Frontend (✅ Complete)
- ✅ Profile page with Telegram connection UI
- ✅ Connect/Disconnect buttons
- ✅ Connection status display
- ✅ Styled notification cards
- ✅ User-friendly instructions

---

## 🎯 To Go Live: 3 Simple Steps

### Step 1: Create Your Bot (5 minutes)

1. **Open Telegram** on your phone
2. **Search for** `@BotFather`
3. **Send:** `/newbot`
4. **Name your bot:** `GramaFix Notifications`
5. **Username:** `your_name_bot` (must end in "bot")
6. **Copy the token** BotFather sends you

Example token: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### Step 2: Configure Backend (2 minutes)

Edit `Backend/.env` and update these lines:

```env
# Replace YOUR_BOT_TOKEN_HERE with the actual token from BotFather
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Replace with your bot's username (without @)
TELEGRAM_BOT_USERNAME=your_name_bot

# Already set to true
ENABLE_TELEGRAM_NOTIFICATIONS=true
```

### Step 3: Set Webhook (Production Only - 3 minutes)

**For local testing:** Skip this step, it works without webhook!

**For production (with a domain):**

Run this command (replace with your values):

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/api/telegram/webhook"}'
```

Or use the Python script in `TELEGRAM_BOT_SETUP.md` (line 88).

---

## 🧪 Test It Right Now!

### Test Flow (Local Development)

1. **Start Backend:**
   ```bash
   cd Backend
   python main.py
   ```

2. **Start Frontend:**
   ```bash
   cd Frontend
   npm run dev
   ```

3. **Login to GramaFix** (create account if needed)

4. **Go to Profile page**

5. **Click "Connect Telegram"** button

6. **In Telegram:**
   - Your bot chat opens automatically
   - Click **START**
   - Bot sends: "🎉 Successfully Connected!"

7. **Go back to Profile** → Should show "✅ Connected"

8. **Report an Issue:**
   - Go to Report Issue page
   - Fill in details and submit
   - **Check Telegram** → You should receive:
     ```
     🆕 Issue Received!
     
     📋 Category: Roads
     📝 Description: Pothole...
     📍 Location: Your GP
     🆔 Issue ID: 12345
     ```

9. **Update Issue Status** (as admin):
   - Go to Admin Dashboard
   - Change status to "In Progress"
   - **Check Telegram** → You should receive:
     ```
     ⚙️ Issue Status Updated!
     
     🆔 Issue ID: 12345
     📋 Category: Roads
     
     🔄 Status Change:
        From: Received
        To: In Progress
     ```

---

## 📋 What Each Notification Looks Like

### 1. Issue Created Notification
```
🆕 Issue Received!

📋 Category: Water Supply
📝 Description: No water supply in sector 5...
📍 Location: Gram Panchayat XYZ
🆔 Issue ID: 67890abcdef12345
⏰ Status: Received

We've received your issue report. Our team will review it shortly.

Thank you for helping improve your community! 🙏
```

### 2. Status Update Notification (In Progress)
```
⚙️ Issue Status Updated!

🆔 Issue ID: 67890abcdef12345
📋 Category: Water Supply

🔄 Status Change:
   From: Received
   To: In Progress

📍 Location: Gram Panchayat XYZ

⚡ Good news! We're working on your issue now.

🔗 View full details on GramaFix
```

### 3. Status Update Notification (Resolved)
```
✅ Issue Status Updated!

🆔 Issue ID: 67890abcdef12345
📋 Category: Water Supply

🔄 Status Change:
   From: In Progress
   To: Resolved

📍 Location: Gram Panchayat XYZ

✨ Great news! Your issue has been resolved. Thank you for your patience!

🔗 View full details on GramaFix
```

### 4. Status Update Notification (Rejected)
```
❌ Issue Status Updated!

🆔 Issue ID: 67890abcdef12345
📋 Category: Water Supply

🔄 Status Change:
   From: Received
   To: Rejected

📍 Location: Gram Panchayat XYZ

❌ Unfortunately, this issue cannot be processed. Please contact support for details.

🔗 View full details on GramaFix
```

---

## 🎨 Profile Page Features

### When Telegram is NOT Connected:
- Shows "🔗 Connect Telegram" button
- Lists benefits (instant notifications, free, etc.)
- Shows simple instructions

### When Telegram IS Connected:
- Shows "✅ Connected" badge with date
- Lists what notifications user will receive
- Shows "Disconnect" button if user wants to unsubscribe

---

## 🔧 Troubleshooting

### Bot Not Responding?
1. **Check token in .env** - Copy-paste carefully from BotFather
2. **Check bot username** - Must match exactly (without @)
3. **Restart backend** - Changes to .env require restart

### Not Receiving Notifications?
1. **Check Telegram connection:**
   - Go to Profile → Should show "✅ Connected"
   - If not, click "Connect Telegram" again

2. **Check backend logs:**
   ```bash
   # Look for messages like:
   # INFO: Telegram message sent successfully to 123456789
   # ERROR: Failed to send Telegram message: ...
   ```

3. **Test manually in Python:**
   ```python
   from telegram_bot import send_telegram_message
   import asyncio
   
   async def test():
       result = await send_telegram_message(
           chat_id="YOUR_CHAT_ID",  # Get from MongoDB
           message="Test from GramaFix! 🎉"
       )
       print(f"Result: {result}")
   
   asyncio.run(test())
   ```

### Webhook Errors (Production)?
1. **Verify URL is HTTPS** - Telegram requires SSL
2. **Check webhook status:**
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
   ```
3. **Look for `last_error_message` in response**
4. **Restart backend after fixing**

---

## 💡 Advanced Features (Optional)

### Custom Messages
Edit `telegram_bot.py` to customize notification templates:
- `notify_issue_created()` - Line 42
- `notify_status_update()` - Line 64
- Add new notification types (high votes, etc.)

### Multiple Languages
Add language parameter to notification functions:
```python
async def notify_issue_created(chat_id, issue_data, language="en"):
    messages = {
        "en": "🆕 Issue Received!",
        "hi": "🆕 समस्या प्राप्त हुई!",
        "ta": "🆕 புகார் பெறப்பட்டது!"
    }
    # Use messages[language] in template
```

### Rich Media
Send photos with notifications:
```python
async with httpx.AsyncClient() as client:
    await client.post(
        f"{TELEGRAM_API_BASE}/sendPhoto",
        json={
            "chat_id": chat_id,
            "photo": image_url,
            "caption": message
        }
    )
```

---

## 📊 Monitor Usage

### Check Connection Rate
```javascript
// In MongoDB
db.users.aggregate([
  { $match: { telegram_chat_id: { $exists: true } } },
  { $group: { 
      _id: { $dateToString: { format: "%Y-%m-%d", date: "$telegram_connected_at" } },
      count: { $sum: 1 }
  }},
  { $sort: { _id: -1 } }
])
```

### Track Notification Success
Add to `telegram_bot.py`:
```python
# After successful send
await notifications_collection.insert_one({
    "user_id": user_id,
    "type": "issue_created",
    "sent_at": datetime.now(),
    "success": True
})
```

---

## 🎯 Success Metrics

After going live, track:
- **Connection Rate:** % of users who connect Telegram
- **Notification Delivery:** Success vs. failure rate
- **User Engagement:** Do users respond faster to issues?
- **Cost Savings:** Compare to SMS costs (if applicable)

---

## 🚀 You're All Set!

Everything is implemented and ready to use. Just:
1. ✅ Create bot with @BotFather
2. ✅ Add token to .env
3. ✅ Restart backend
4. ✅ Test with your account

**Estimated setup time:** 10-15 minutes  
**Cost:** $0.00 forever  
**Maintenance:** Near zero  

🎉 **Enjoy free, instant notifications!** 🎉

---

## 📚 Additional Resources

- **Full Setup Guide:** See `TELEGRAM_BOT_SETUP.md` for detailed instructions
- **Telegram Bot API:** https://core.telegram.org/bots/api
- **python-telegram-bot Docs:** https://docs.python-telegram-bot.org/
- **BotFather Commands:** `/help` in @BotFather chat

---

**Questions?** Check the troubleshooting section or review the setup guide.
