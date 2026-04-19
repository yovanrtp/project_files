from flask import Blueprint

leads_bp = Blueprint('leads', __name__)

@leads_bp.route('/')
def index():
    return "Leads module"
