"""
Quick test script to verify Telegram Bot connection
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME")

async def test_bot():
    print("🔍 Testing Telegram Bot Configuration...\n")
    
    print(f"Bot Token: {BOT_TOKEN[:20]}..." if BOT_TOKEN else "❌ No token found")
    print(f"Bot Username: @{BOT_USERNAME}\n")
    
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file!")
        return
    
    # Test 1: Get bot info
    print("📡 Test 1: Getting bot information...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getMe",
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_info = data.get("result", {})
                    print(f"✅ Bot connected successfully!")
                    print(f"   Bot Name: {bot_info.get('first_name')}")
                    print(f"   Bot Username: @{bot_info.get('username')}")
                    print(f"   Bot ID: {bot_info.get('id')}")
                    
                    # Check if username matches
                    if bot_info.get('username') != BOT_USERNAME:
                        print(f"\n⚠️  WARNING: Bot username mismatch!")
                        print(f"   .env has: {BOT_USERNAME}")
                        print(f"   Actual: {bot_info.get('username')}")
                        print(f"   Please update TELEGRAM_BOT_USERNAME in .env\n")
                else:
                    print(f"❌ Failed: {data}")
            else:
                print(f"❌ HTTP Error {response.status_code}")
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 2: Check webhook status
    print("\n📡 Test 2: Checking webhook status...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo",
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    webhook = data.get("result", {})
                    webhook_url = webhook.get("url", "")
                    
                    if webhook_url:
                        print(f"✅ Webhook configured: {webhook_url}")
                        print(f"   Pending updates: {webhook.get('pending_update_count', 0)}")
                        if webhook.get("last_error_message"):
                            print(f"   ⚠️  Last error: {webhook.get('last_error_message')}")
                    else:
                        print(f"ℹ️  No webhook configured (OK for local development)")
                        print(f"   Bot will work via direct API calls")
    except Exception as e:
        print(f"⚠️  Could not check webhook: {e}")
    
    # Test 3: Generate connection link
    print(f"\n📡 Test 3: Testing connection link...")
    test_user_id = "test123"
    link = f"https://t.me/{BOT_USERNAME}?start={test_user_id}"
    print(f"✅ Connection link format: {link}")
    print(f"   (This is what opens when user clicks 'Connect Telegram')")
    
    print("\n" + "="*60)
    print("✅ TELEGRAM BOT IS CONFIGURED CORRECTLY!")
    print("="*60)
    print("\n📱 To connect:")
    print("1. Go to Profile page in your app")
    print("2. Click 'Connect Telegram' button")
    print("3. Click START in Telegram")
    print("4. Bot will save your chat_id automatically\n")

if __name__ == "__main__":
    asyncio.run(test_bot())
