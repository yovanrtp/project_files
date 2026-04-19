from flask import Blueprint

contacts_bp = Blueprint('contacts', __name__)

@contacts_bp.route('/')
def index():
    return "Contacts module"
