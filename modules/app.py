from flask import Flask
from modules.leads import leads_bp
from modules.contacts import contacts_bp
from modules.accounts import accounts_bp
from modules.deals import deals_bp
from modules.tasks import tasks_bp
from modules.meetings import meetings_bp
from modules.documents import documents_bp
from modules.projects import projects_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(leads_bp, url_prefix='/leads')
app.register_blueprint(contacts_bp, url_prefix='/contacts')
app.register_blueprint(accounts_bp, url_prefix='/accounts')
app.register_blueprint(deals_bp, url_prefix='/deals')
app.register_blueprint(tasks_bp, url_prefix='/tasks')
app.register_blueprint(meetings_bp, url_prefix='/meetings')
app.register_blueprint(documents_bp, url_prefix='/documents')
app.register_blueprint(projects_bp, url_prefix='/projects')

@app.route('/')
def hello():
    return "Hello, Modular Dockerized Flask App!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
