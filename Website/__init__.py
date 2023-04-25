from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

db = SQLAlchemy()
DB_Name = "Database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'My secret key'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_Name}'
    db.init_app(app)

    
    from .auth import auth  

     
    app.register_blueprint(auth, url_prefix = '/')  

    from .models import User
    create_database(app)

    # from models import User
    login_manager = LoginManager()
    login_manager.login_view = 'auth.Login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app 


def create_database(app):
    if not path.exists('instance/' + DB_Name):
        db.create_all(app=app)
        print("Database Created!") 
        