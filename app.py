from flask import Flask, redirect, url_for
from flask_login import LoginManager
from config import Config
from models import db, User

login_manager = LoginManager()
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    login_manager.init_app(app)

    from auth import bp as auth_bp
    from tickets import bp as tickets_bp
    from admin_panel import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def index():
        return redirect(url_for("tickets.list_tickets"))

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        from seed import seed
        seed()
    app.run(debug=False)