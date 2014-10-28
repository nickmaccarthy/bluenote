from flask import Flask
#from sqlalchemy import create_engine, MetaData
#from flask.ext.login import LoginManager

app = Flask(__name__)
app.debug = True

#app.config.from_object('app.config')

#login_manager = LoginManager()
#login_manager.init_app(app)

from app import views

#login_manager.login_view = "login"
