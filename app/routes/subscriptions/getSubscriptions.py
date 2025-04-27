from ... import db
from flask import Blueprint, jsonify, request
from ...models import Subscription
from . import subscriptions_bp
from sqlalchemy.exc import SQLAlchemyError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@subscriptions_bp.route('/getsubscriptions', methods=['GET'])
def get_subscriptions():
    try:
        logger.info('Fetching all subscriptions')
        subscriptions = Subscription.query.all()
        if not subscriptions:
            logger.warning('No subscriptions found')
            return jsonify({'message': 'No subscriptions found'}), 404
        
        logger.info(f'Found {len(subscriptions)} subscriptions')
        subscription_list = [subscription.to_dict() for subscription in subscriptions]
        logger.info(f'Subscription list: {subscription_list}')
        return jsonify({'subscriptions': subscription_list}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f'Error fetching subscriptions: {str(e)}')
        return jsonify({'error': str(e)}), 500