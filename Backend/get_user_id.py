"""
Get your user ID to connect Telegram manually
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def get_user_id():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017/GramaFix")
    db = client["GramaFix"]
    users = db["users"]
    
    # Get all users
    print("📋 Users in database:\n")
    async for user in users.find():
        user_id = str(user["_id"])
        name = user.get("name", "Unknown")
        phone = user.get("phone", "No phone")
        telegram_connected = "✅ Connected" if user.get("telegram_chat_id") else "❌ Not connected"
        
        print(f"Name: {name}")
        print(f"Phone: {phone}")
        print(f"User ID: {user_id}")
        print(f"Telegram: {telegram_connected}")
        print("-" * 50)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(get_user_id())
