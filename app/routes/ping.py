from flask import Blueprint, jsonify
from .. import db
from sqlalchemy import inspect

ping_bp = Blueprint('ping', __name__)

@ping_bp.route('/ping', methods=['GET'])
def ping():
    # Get the inspector to query for table names
    inspector = inspect(db.engine)
    
    # Get all table names
    table_names = inspector.get_table_names()
    
    return jsonify({
        'message': 'pong',
        'database': {
            'tables': table_names
        }
    }), 200
    
    
@ping_bp.route('/ping/cleardb', methods=['GET'])
def clear_db():
    db.drop_all()
    db.create_all()
    return jsonify({
        'message': 'Database cleared and recreated'
    }), 200