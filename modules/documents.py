from flask import Blueprint

documents_bp = Blueprint('documents', __name__)

@documents_bp.route('/')
def index():
    return "Documents module"
