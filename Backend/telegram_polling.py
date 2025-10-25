"""
Telegram Bot Polling Service - Run this to make bot respond automatically
This allows the bot to work on localhost without webhooks
"""
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/GramaFix")

# MongoDB connection
client = AsyncIOMotorClient(MONGO_URI)
db = client["GramaFix"]
users_collection = db["users"]

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    chat_id = str(update.effective_chat.id)
    
    # Check if there's a user_id parameter
    if context.args and len(context.args) > 0:
        user_id = context.args[0]
        
        try:
            # Update user's telegram_chat_id
            result = await users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "telegram_chat_id": chat_id,
                    "telegram_connected_at": datetime.now()
                }}
            )
            
            if result.modified_count > 0:
                # Send welcome message
                await update.message.reply_text(
                    "🎉 <b>Successfully Connected!</b>\n\n"
                    "Your GramaFix account is now linked to Telegram.\n\n"
                    "You'll receive instant notifications when:\n"
                    "• Your issues are reviewed\n"
                    "• Status updates occur\n"
                    "• Issues are resolved\n\n"
                    "Thank you for using GramaFix! 🙏",
                    parse_mode='HTML'
                )
                print(f"✅ User {user_id} connected with chat_id {chat_id}")
            else:
                await update.message.reply_text(
                    "❌ User not found. Please try reconnecting from the GramaFix website."
                )
                print(f"❌ User {user_id} not found in database")
                
        except Exception as e:
            print(f"❌ Error connecting user: {e}")
            await update.message.reply_text(
                "❌ Connection failed. Please try again later."
            )
    else:
        # No user_id provided
        await update.message.reply_text(
            "👋 Hello! To connect your GramaFix account:\n\n"
            "1. Go to your Profile page on GramaFix\n"
            "2. Click 'Connect Telegram' button\n"
            "3. Click START when Telegram opens\n\n"
            "Or use: /start YOUR_USER_ID"
        )

async def disconnect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /disconnect command"""
    chat_id = str(update.effective_chat.id)
    
    result = await users_collection.update_one(
        {"telegram_chat_id": chat_id},
        {"$unset": {"telegram_chat_id": "", "telegram_connected_at": ""}}
    )
    
    if result.modified_count > 0:
        await update.message.reply_text(
            "✅ Telegram disconnected successfully. "
            "You won't receive notifications anymore."
        )
        print(f"✅ Chat {chat_id} disconnected")
    else:
        await update.message.reply_text(
            "⚠️ No connected account found."
        )

async def main():
    """Start the bot with polling"""
    print("🤖 Starting Telegram Bot in Polling Mode...")
    print(f"📱 Bot: @{os.getenv('TELEGRAM_BOT_USERNAME')}")
    print("=" * 60)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("disconnect", disconnect_command))
    
    # Start polling
    print("✅ Bot is running and listening for commands...")
    print("💡 Users can now connect via the website!")
    print("🛑 Press Ctrl+C to stop\n")
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping bot...")
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
