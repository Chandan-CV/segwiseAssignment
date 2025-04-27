from flask import Blueprint, jsonify, request
from . import subscriptions_bp
from ... import db
from ...models import Subscription
from sqlalchemy.exc import SQLAlchemyError
import os

@subscriptions_bp.route('/createsubscription', methods=['POST'])
def create_subscription():
    data = request.get_json()
    required_fields = ['url', 'secret']
    
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    url = data.get('url')
    secret = data.get('secret')
    
    try:
        # Create new subscription
        subscription = Subscription(url=url)
        
        # Handle secret with proper hashing
        if secret:
            subscription.set_secret(secret)
        else:
            # Auto-generate a secure secret if none provided
            auto_secret = os.urandom(16).hex()
            subscription.set_secret(auto_secret)
            
        db.session.add(subscription)
        db.session.commit()
        
        response_data = {
            'message': 'Subscription created successfully',
            'subscription': {
                'id': subscription.id,
                'url': subscription.url,
                'created_at': subscription.created_at.isoformat()
            }
        }
        
        # Include the generated secret in response (only shown once)
        if not secret:
            response_data['secret'] = auto_secret
        
        return jsonify(response_data), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500