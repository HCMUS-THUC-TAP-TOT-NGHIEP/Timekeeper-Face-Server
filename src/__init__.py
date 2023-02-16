from flask import Flask
app = Flask(__name__)

from authentication import Authentication

# Registering blueprints
app.register_blueprint(Authentication)