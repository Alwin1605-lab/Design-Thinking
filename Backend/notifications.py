"""
Deprecated notifications module.

This file was previously used to forward notification events to n8n or FCM.
Both n8n and FCM integrations were intentionally removed from the project.
The module remains as a no-op placeholder to avoid import/runtime errors in
older branches. Do not add production notification logic here.
"""

def deprecated_notification_stub(*args, **kwargs):
    return False


async def send_n8n_email(*args, **kwargs):
    return False


async def notify_issue_created(*args, **kwargs):
    return False


async def notify_status_updated(*args, **kwargs):
    return False
