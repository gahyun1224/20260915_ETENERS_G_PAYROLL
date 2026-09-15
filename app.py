import os

from flask import Flask

from config import Config
from extensions import db, login_manager


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    if not os.environ.get("VERCEL"):
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"), exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)

    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes import auth, dashboard, history, rules, upload

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(upload.bp)
    app.register_blueprint(history.bp)
    app.register_blueprint(rules.bp)

    with app.app_context():
        db.create_all()
        from seed_data import seed_rules, seed_users

        seed_rules()
        seed_users()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5100)
