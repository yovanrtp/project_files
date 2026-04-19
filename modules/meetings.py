from flask import Blueprint

meetings_bp = Blueprint('meetings', __name__)

@meetings_bp.route('/')
def index():
    return "Meetings module"
