from flask import Flask, request, session, flash, g, redirect, url_for
import os
import datetime

import db_handler
import transactions_handler

# Import Blueprints
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.api_routes import api_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # Replace with a strong, static secret key in production

# Initialize database
db_handler.init_db()
transactions_handler.init_asset_types()  # Ensure asset types are initialized

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db_handler.get_user_by_id(user_id)

# Define the custom Jinja2 filter
@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    try:
        # Convert the timestamp to a readable date
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return "Invalid date"

# Register the filter with the app
app.jinja_env.filters['timestamp_to_date'] = timestamp_to_date

# Register Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)  # auth_bp has /login, /register, /logout
app.register_blueprint(api_bp, url_prefix='/api')  # api_bp has its own url_prefix defined

if __name__ == '__main__':
    app.run(debug=True)
