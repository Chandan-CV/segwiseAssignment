from ... import db
from flask import Blueprint, jsonify, request
from ...models import Subscription
from . import subscriptions_bp
from sqlalchemy.exc import SQLAlchemyError

@subscriptions_bp.route('/deletesubscription', methods=['DELETE'])
def delete_subscription():
    data = request.get_json()
    required_fields = ['id']
    
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        subscription = Subscription.query.get(data['id'])
        if not subscription:
            return jsonify({'error': 'Subscription not found'}), 404

        db.session.delete(subscription)
        db.session.commit()
        
        return jsonify({'message': 'Subscription deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500