from flask import Blueprint, jsonify, request
from .. import db
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from ..models import Subscription, WebhookPayload
from ..tasks import process_webhook_delivery
import logging
import hmac
import hashlib
import json
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a blueprint for the ingest route
ingest_bp = Blueprint('ingest', __name__)


@ingest_bp.route('/ingest/bypass-signature/<sub_id>', methods=['POST'])
def ingest_bypass_signature(sub_id):
    """
    Ingest route that bypasses signature verification.
    This is for testing purposes only and should not be used in production.
    """
    # Get the request data
    payload = request.get_json()
    
    if not payload:
        return jsonify({'error': 'Invalid JSON payload'}), 400
    
    try:
        subscription = Subscription.query.get(sub_id)
    except ValueError:
        return jsonify({'error': 'Invalid subscription ID'}), 400
    
    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404
    
    # Create webhook payload record
    webhook_payload = WebhookPayload(
        subscription_id=int(sub_id),
        payload=payload,
    )
    db.session.add(webhook_payload)
    db.session.commit()
    webhook_id = webhook_payload.id
    
    # Queue for asynchronous processing
    process_webhook_delivery.delay(webhook_id)
        
    logger.info(f"Webhook {webhook_id} received for subscription {sub_id} and queued for delivery")
    
    return jsonify({
        'status': 'accepted',
        'webhook_id': webhook_id,
        'subscription_id': sub_id
    }), 202


# Define the ingest route
@ingest_bp.route('/ingest/<sub_id>', methods=['POST'])
def ingest(sub_id):
    # Get the request data
    payload_bytes = request.get_data()
    payload = request.get_json()
    
    if not payload:
        return jsonify({'error': 'Invalid JSON payload'}), 400
    
    try:
        subscription = Subscription.query.get(sub_id)
    except ValueError:
        return jsonify({'error': 'Invalid subscription ID'}), 400
    
    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404
    
    # Verify signature if secret_hash is set
    if subscription.secret_hash:
        # Get signature from header
        signature_header = request.headers.get('X-Hub-Signature-256')
        
        if not signature_header:
            logger.warning(f"Webhook for subscription {sub_id} received without signature")
            return jsonify({'error': 'Missing signature header for subscription with secret key'}), 401
        
        # Verify the signature
        valid_signature = verify_signature(payload_bytes, signature_header, subscription)
        
        if not valid_signature:
            logger.warning(f"Invalid signature for subscription {sub_id}")
            return jsonify({'error': 'Invalid signature'}), 401
        
        logger.info(f"Signature verified for subscription {sub_id}")
    
    # Create webhook payload record
    webhook_payload = WebhookPayload(
        subscription_id=int(sub_id),
        payload=payload,
    )
    db.session.add(webhook_payload)
    db.session.commit()
    webhook_id = webhook_payload.id
    
    # Queue for asynchronous processing
    process_webhook_delivery.delay(webhook_id)
        
    logger.info(f"Webhook {webhook_id} received for subscription {sub_id} and queued for delivery")
    
    return jsonify({
        'status': 'accepted',
        'webhook_id': webhook_id,
        'subscription_id': sub_id
    }), 202

def verify_signature(payload_bytes, signature_header, subscription):
    """
    Verify the signature of a webhook payload
    """
    if not signature_header.startswith('sha256='):
        return False
    
    provided_signature = signature_header[7:]  # Remove 'sha256=' prefix
    
    # Make sure we have a secret to verify with
    if not subscription.secret:  # Use secret, not secret_hash
        logger.error(f"Missing secret for subscription {subscription.id}")
        return False
    
    # Calculate HMAC signature using the raw secret
    expected_signature = hmac.new(
        key=subscription.secret.encode('utf-8'),  # Use raw secret, not hash
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Compare signatures using constant-time comparison
    return hmac.compare_digest(expected_signature, provided_signature)


@ingest_bp.route('/ingest/getsignature', methods=['POST'])
def generate_signature():
    """
    Generate a signature for testing webhook signature verification.
    Accepts a JSON payload with 'payload' and 'secret' fields.
    Returns the signature and example curl command.
    
    Example request:
    ```
    {
        "payload": {"event":"test_event","data":{"hello":"world"}},
        "secret": "helloworld"
    }
    ```
    """
    # Get request data
    request_data = request.get_json()
    
    if not request_data:
        return {'error': 'Invalid JSON request'}, 400
        
    # Extract payload and secret
    payload = request_data.get('payload')
    secret = request_data.get('secret')
    
    if not payload:
        return {'error': 'Missing payload field'}, 400
    if not secret:
        return {'error': 'Missing secret field'}, 400
        
    # Convert payload to string if it's a dictionary
    if isinstance(payload, dict):
        payload_str = json.dumps(payload, separators=(',', ':'))  # compact JSON with no whitespace
    else:
        payload_str = str(payload)
        
    # Calculate the signature
    signature = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload_str.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Prepare response with signature and examples
   
    return {'signature':f'sha256={signature}'}, 200