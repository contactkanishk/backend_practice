from flask import Flask
from config import Config
from extensions import bcrypt, jwt, mail, cors
from routes.auth import auth_bp
from routes.questions import questions_bp

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
bcrypt.init_app(app)
jwt.init_app(app)
mail.init_app(app)
cors.init_app(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(questions_bp)

if __name__ == "__main__":
    app.run(debug=True)
