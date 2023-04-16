from flask import *
import requests
from dotenv import load_dotenv, find_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user

load_dotenv(find_dotenv())

app = Flask(__name__)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return Gamer.query.get(int(id))

#DATABASE MODELS
class Gamer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    
    def is_active(self):
        return True
    
class Groups(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    members = db.Column(db.String(800), nullable=False)
    availabilities = db.Column(db.String(800))

with app.app_context():
    db.create_all()
    


@app.route('/', methods = ['POST', 'GET'])
def landing():
    
    
@app.route('/login')
def login():
    
    
@app.route('/register')
def register():
    
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route('/group', methods = ['POST', 'GET'])
def group_number():
    

@app.route('/group/<group_number>', methods = ['POST', 'GET'])
def gamer_group(group_number):