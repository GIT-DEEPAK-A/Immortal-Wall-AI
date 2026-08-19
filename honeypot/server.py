# honeypot/server.py

from flask import Flask
from honeypot.routes.login import login_bp
from honeypot.routes.dashboard import dashboard_bp

def create_honeypot_app():
    app = Flask(__name__)
    app.register_blueprint(login_bp)
    app.register_blueprint(dashboard_bp)
    return app

if __name__ == "__main__":
    app = create_honeypot_app()
    app.run(host="0.0.0.0", port=5001, debug=True)