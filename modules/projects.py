from flask import Blueprint

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/')
def index():
    return "Projects module"
