from celery import Celery
import os
import requests
from datetime import datetime
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_celery(app_name= __name__):
    redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    return Celery(
        app_name,
        broker=redis_url,
        backend=redis_url,
    )

celery = make_celery()


RETRY_DELAYS = [10, 30, 60, 300, 900]  # 10s, 30s, 1m, 5m, 15m
MAX_RETRIES = len(RETRY_DELAYS)

@celery.task(bind=True, max_retries=MAX_RETRIES)
def process_webhook_delivery(self, webhook_id):
    
    from app import db
    from app.models import WebhookPayload, Subscription, DeliveryAttempt
    
    logger.info(f'Processing webhook {webhook_id}, attempt {self.request.retries +1} ')
    
    try:
        
        webhook = WebhookPayload.query.get(webhook_id) 
        if not webhook:
            logger.error(f'Webhook {webhook_id} not found')
            return {status: 'error', message: f'Webhook {webhook_id} not found'}
        
        subscription = Subscription.query.get(webhook.subscription_id)
        if not subscription:
            logger.error(f'Subscription {webhook.subscription_id} not found')
            return {status: 'error', message: f'Subscription {webhook.subscription_id} not found'}
        
        attempt_number = self.request.retries + 1
        
        delivery_attempt = DeliveryAttempt(
            webhook_id=webhook.id,
            subscription_id=subscription.id,
            attempt_number=attempt_number,
            status='in_progress'
        )
        
        db.session.add(delivery_attempt)
        db.session.commit()
        
        try:
            
            response = requests.post(
                subscription.url,
                json=webhook.payload,
                headers={'Content-Type': 'application/json', 'X-Hub-Signature': subscription.secret},
                timeout=10
            )
            
            delivery_attempt.status_code = response.status_code

            if 200 <= response.status_code < 300:
                delivery_attempt.status = 'success'
                delivery_attempt.response_body = response.text
                db.session.commit()
                logger.info(f'Webhook {webhook_id} delivered successfully')
                return {
                    'status': 'success', 
                    'message': f'Webhook {webhook_id} delivered successfully',
                    'subscription_id': subscription.id,
                    }
                
            
            
            error_message = f"Target returned non-success status: HTTP {response.status_code}"
            delivery_attempt.status = 'failed'
            delivery_attempt.error_message = error_message
            db.session.commit()
            
            # Raise exception to trigger retry mechanism
            raise Exception(error_message)

        except (requests.RequestException, Exception) as e:
            # Handle request exceptions (timeouts, connection errors, etc.)
            error_message = str(e)
            logger.warning(f"Delivery failed for webhook {webhook_id}: {error_message}")
            
            # Update delivery attempt with error
            delivery_attempt.status = 'failed'
            delivery_attempt.error_message = error_message[:500]  # Limit size
            db.session.commit()
            
            # Check if we should retry
            if attempt_number < MAX_RETRIES:
                # Calculate retry delay
                retry_delay = RETRY_DELAYS[attempt_number - 1]
                
                logger.info(f"Scheduling retry {attempt_number + 1} in {retry_delay}s for webhook {webhook_id}")
                
                # Retry with backoff delay
                raise self.retry(exc=e, countdown=retry_delay)
            else:
                # All retries exhausted - mark as permanent failure
                logger.error(f"All retry attempts exhausted for webhook {webhook_id}")
                return {
                    "status": "failure",
                    "webhook_id": webhook_id,
                    "attempts": attempt_number,
                    "error": error_message
                }
    
    except Exception as e:
        logger.exception(f"Unexpected error processing webhook {webhook_id}: {str(e)}")
        return {"status": "error", "message": str(e)}