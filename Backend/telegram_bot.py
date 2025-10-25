"""
Telegram Bot Integration for GramaFix Issue Notifications
Free, instant notifications via Telegram
"""
import os
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ENABLE_TELEGRAM = os.getenv("ENABLE_TELEGRAM_NOTIFICATIONS", "true").lower() == "true"
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


async def send_telegram_message(chat_id: str, message: str, parse_mode: str = "HTML") -> bool:
    """
    Send a message to a Telegram user
    
    Args:
        chat_id: Telegram chat ID of the user
        message: Message text (supports HTML formatting)
        parse_mode: "HTML" or "Markdown"
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not ENABLE_TELEGRAM or not TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram notifications disabled or bot token not configured")
        return False
    
    if not chat_id:
        logger.warning("No chat_id provided")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEGRAM_API_BASE}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                logger.info(f"Telegram message sent successfully to {chat_id}")
                return True
            else:
                logger.error(f"Failed to send Telegram message: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error sending Telegram message: {str(e)}")
        return False


async def notify_issue_created(chat_id: str, issue_data: dict) -> bool:
    """
    Send notification when a new issue is created
    """
    message = f"""
🆕 <b>Issue Received!</b>

📋 <b>Category:</b> {issue_data.get('category', 'N/A')}
📝 <b>Description:</b> {issue_data.get('description', 'N/A')[:200]}
📍 <b>Location:</b> {issue_data.get('gram_panchayat', 'N/A')}
🆔 <b>Issue ID:</b> {issue_data.get('issue_id', 'N/A')}
⏰ <b>Status:</b> Received

We've received your issue report. Our team will review it shortly.

Thank you for helping improve your community! 🙏
"""
    return await send_telegram_message(chat_id, message)


async def notify_status_update(chat_id: str, issue_data: dict, new_status: str, old_status: str) -> bool:
    """
    Send notification when issue status changes
    """
    status_emoji = {
        "Received": "📥",
        "In Progress": "⚙️",
        "Resolved": "✅",
        "Rejected": "❌"
    }
    
    emoji = status_emoji.get(new_status, "📢")
    
    message = f"""
{emoji} <b>Issue Status Updated!</b>

🆔 <b>Issue ID:</b> {issue_data.get('issue_id', 'N/A')}
📋 <b>Category:</b> {issue_data.get('category', 'N/A')}

🔄 <b>Status Change:</b>
   From: {old_status}
   To: <b>{new_status}</b>

📍 <b>Location:</b> {issue_data.get('gram_panchayat', 'N/A')}
"""
    
    if new_status == "Resolved":
        message += "\n✨ Great news! Your issue has been resolved. Thank you for your patience!"
    elif new_status == "In Progress":
        message += "\n⚡ Good news! We're working on your issue now."
    elif new_status == "Rejected":
        message += "\n❌ Unfortunately, this issue cannot be processed. Please contact support for details."
    
    message += "\n\n🔗 <i>View full details on GramaFix</i>"
    
    return await send_telegram_message(chat_id, message)


async def notify_high_votes(chat_id: str, issue_data: dict, vote_count: int) -> bool:
    """
    Send notification when an issue receives significant community votes
    """
    message = f"""
🔥 <b>Your Issue is Trending!</b>

🆔 <b>Issue ID:</b> {issue_data.get('issue_id', 'N/A')}
📋 <b>Category:</b> {issue_data.get('category', 'N/A')}

👥 <b>Community Votes:</b> {vote_count}

Your issue has received attention from the community! This helps prioritize action.

📍 <b>Location:</b> {issue_data.get('gram_panchayat', 'N/A')}
"""
    return await send_telegram_message(chat_id, message)


def get_telegram_bot_link(user_id: str) -> str:
    """
    Generate a deep link for users to connect their Telegram
    
    Args:
        user_id: User's ID from your database
    
    Returns:
        str: Telegram bot link with start parameter
    """
    if not TELEGRAM_BOT_TOKEN:
        return ""
    
    # Extract bot username from token (before the colon)
    # You'll need to set this manually or get it from bot info
    bot_username = os.getenv("TELEGRAM_BOT_USERNAME", "YourBotName")
    
    return f"https://t.me/{bot_username}?start={user_id}"


async def verify_telegram_chat(chat_id: str) -> bool:
    """
    Verify that a chat_id is valid and bot can send messages to it
    """
    if not ENABLE_TELEGRAM or not TELEGRAM_BOT_TOKEN:
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEGRAM_API_BASE}/getChat",
                json={"chat_id": chat_id},
                timeout=5.0
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Error verifying Telegram chat: {str(e)}")
        return False
