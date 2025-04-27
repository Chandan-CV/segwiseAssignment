from flask import Blueprint, jsonify, request
clients_bp = Blueprint('clients', __name__)
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@clients_bp.route('/clients/<client_id>', methods=['POST'])
def handler(client_id):
    data = request.get_json()
    logger.info(f'Received data for client {client_id}: {data}')
    return jsonify({
        'message': 'Client data received',
        'client_id': client_id,
        'data': data
    }), 200
