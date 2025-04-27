from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from flask_migrate import Migrate


db = SQLAlchemy()
migrate = Migrate()
def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/wds')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    migrate.init_app(app, db)
    from .routes import ping_bp, subscriptions_bp, clients_bp, ingest_bp, swagger_bp, logs_bp
   
    
    app.register_blueprint(ping_bp)
    app.register_blueprint(subscriptions_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(ingest_bp)
    app.register_blueprint(swagger_bp)
    app.register_blueprint(logs_bp)
    with app.app_context():
        db.create_all()
    
    return app
