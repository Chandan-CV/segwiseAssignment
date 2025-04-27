from flask import Blueprint
subscriptions_bp = Blueprint('subscriptions', __name__, url_prefix='/subscriptions')
from .createsubscription import *
from .getSubscriptions import *
from .updateSubsctiption import *
from .deleteSubscription import *