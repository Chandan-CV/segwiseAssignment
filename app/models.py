from . import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
import uuid
import os
import hashlib
import hmac
from sqlalchemy.ext.declarative import declarative_base


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    
    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False)
    secret = Column(String(128), nullable=True)  # For HMAC verification
    secret_hash = Column(String(128), nullable=True)  # For secure storage
    salt = Column(String(64), nullable=True)  # Random salt for each subscription
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @staticmethod
    def generate_salt():
        """Generate a random salt for password hashing"""
        return os.urandom(32).hex()
    
    @staticmethod
    def hash_secret(secret, salt):
        """Hash a secret with the given salt using SHA-256"""
        if not secret:
            return None
        
        # Create a salted hash
        hash_obj = hashlib.sha256()
        hash_obj.update(salt.encode('utf-8'))
        hash_obj.update(secret.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def set_secret(self, secret):
        """Set the secret, generating a salt and storing the hash"""
        if secret:
            self.secret = secret  # Store raw secret for HMAC verification
            self.salt = self.generate_salt()
            self.secret_hash = self.hash_secret(secret, self.salt)  # For secure storage
        else:
            self.secret = None
            self.salt = None
            self.secret_hash = None
    
    def verify_signature(self, payload_bytes, signature):
        """Verify a webhook signature using the stored secret"""
        if not self.secret or not signature:
            return False
            
        # Extract hash algorithm and value from signature header
        if not signature.startswith('sha256='):
            return False
            
        provided_sig = signature[7:]  # Remove 'sha256=' prefix
        
        # Use the RAW secret for HMAC verification
        hmac_obj = hmac.new(
            self.secret.encode('utf-8'),  # Use raw secret, not hashed
            payload_bytes,
            hashlib.sha256
        )
        expected_sig = hmac_obj.hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(provided_sig, expected_sig)
    def __repr__(self):
        return f'<Subscription {self.id}>'
    
    def to_dict(self):
        return {
            'id':self.id,
            'url': self.url,
            'secret_hash': self.secret_hash,
            'salt': self.salt,
            'created_at': self.created_at.isoformat() if self.created_at else None
            
        }
        




class WebhookPayload(db.Model):
    __tablename__ = 'webhook_payloads'
    
    id = Column(String(36), primary_key=True, default =  lambda: str(uuid.uuid4()))  # UUID as string
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=False)
    payload = Column(db.JSON, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)  # Unix timestamp
    
    # Relationships
    subscription = db.relationship(Subscription, backref='webhook_payloads')
    
    def __repr__(self):
        return f'<WebhookPayload {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'subscription_id': self.subscription_id,
            'payload': self.payload,
            'received_at': self.received_at
        }


class Logs(db.Model):
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True)
    wp_id = Column(String(36), ForeignKey('webhook_payloads.id'), nullable=False)
    log_message = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subscription = db.relationship(WebhookPayload, backref='logs')
    
    def __repr__(self):
        return f'<Log {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'wp_id': self.wp_id,
            'log_message': self.log_message,
            'created_at': self.created_at
        }
# Add to your models.py file
class DeliveryAttempt(db.Model):
    __tablename__ = 'delivery_attempts'
    
    id = Column(Integer, primary_key=True)
    webhook_id = Column(String(36), ForeignKey('webhook_payloads.id'), nullable=False)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)  # in_progress, success, failed
    timestamp = Column(DateTime, default=datetime.utcnow)
    status_code = Column(Integer, nullable=True)
    error_message = Column(String(500), nullable=True)
    response_body = Column(String(500), nullable=True)
    
    # Create indexes for frequent queries
    __table_args__ = (
        db.Index('idx_delivery_webhook_id', webhook_id),
        db.Index('idx_delivery_subscription_id', subscription_id),
    )
    
    def __repr__(self):
        return f'<DeliveryAttempt {self.id} for webhook {self.webhook_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'webhook_id': self.webhook_id,
            'subscription_id': self.subscription_id,
            'attempt_number': self.attempt_number,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'status_code': self.status_code,
            'error_message': self.error_message,
            'response_body': self.response_body
        }