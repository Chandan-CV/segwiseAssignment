from flask import Blueprint, jsonify
from . import db
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
import logging
from .models import DeliveryAttempt

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a blueprint for the logs route
logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/logs/deliverylogs', methods=['GET'])
def get_delivery_logs():
    """
    Fetch all delivery logs from the database.
    """
    try:
        logger.info('Fetching all delivery logs')
        # Assuming you have a DeliveryLog model 
        # order by timestamp
        delivery_logs = db.session.query(DeliveryAttempt).order_by(DeliveryAttempt.timestamp.desc()).all()
        if not delivery_logs:
            logger.warning('No delivery logs found')
            return jsonify({'message': 'No delivery logs found'}), 404
        
        logger.info(f'Found {len(delivery_logs)} delivery logs')
        log_list = [log.to_dict() for log in delivery_logs]
        logger.info(f'Delivery log list: {log_list}')
        return jsonify({'delivery_logs': log_list}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f'Error fetching delivery logs: {str(e)}')
        return jsonify({'error': str(e)}), 500