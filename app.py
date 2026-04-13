import os
from flask import Flask
from dotenv import load_dotenv

# Load blueprints
from blueprints.auth import auth_bp
from blueprints.main import main_bp
from blueprints.analyzer import analyzer_bp
from blueprints.timetable import timetable_bp
from blueprints.optimizer import optimizer_bp

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'super_secret_dev_key')

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(analyzer_bp)
    app.register_blueprint(timetable_bp)
    app.register_blueprint(optimizer_bp)

    return app

app = create_app()

if __name__ == '__main__':
    # Increase recursion depth for complex timetable backtracking if needed
    import sys
    sys.setrecursionlimit(2000)
    
    app.run(debug=True, port=5000, host="0.0.0.0")
