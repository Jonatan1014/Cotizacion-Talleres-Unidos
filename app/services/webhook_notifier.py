# document_processor/app/services/webhook_notifier.py
import requests
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_webhook_notification(webhook_url: str, payload: Dict[Any, Any]):
    """
    Send webhook notification with processing results
    """
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=settings.WEBHOOK_TIMEOUT,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code not in [200, 201, 204]:
            logger.warning(f"Webhook notification failed with status {response.status_code}: {response.text}")
        else:
            logger.info(f"Webhook notification sent successfully to {webhook_url}")
            
    except requests.exceptions.Timeout:
        logger.error(f"Webhook notification timed out for URL: {webhook_url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Webhook notification failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during webhook notification: {str(e)}")