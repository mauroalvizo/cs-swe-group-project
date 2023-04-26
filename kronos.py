from flask import *
import os
from dotenv import load_dotenv, find_dotenv
import random
import string
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt


load_dotenv(find_dotenv())

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("HIDDEN_KEY")
app.secret_key = secrets.token_hex(16)


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    return Gamer.query.get(int(id))

#FOR CREATING THE RANDOM team CODE
code_length = 10
characters = string.ascii_letters + string.digits

#DATABASE MODELS
class Gamer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(122), nullable=False)
    
    def is_active(self):
        return True
    
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    team_code = db.Column(db.String(10), nullable=False, unique=True)
    team_name = db.Column(db.String(80), nullable=False)
    number_of_members = db.Column(db.Integer, nullable=False)
    
class TeamMember(db.Model):
    gamer_id = db.Column(db.Integer, db.ForeignKey('gamer.id'), primary_key=True)
    team_code = db.Column(db.String(10), db.ForeignKey('team.team_code'), primary_key=True)
    gamer = db.relationship('Gamer', backref=db.backref('team_members', lazy=True))
    team = db.relationship('Team', backref=db.backref('team_members', lazy=True))
    
class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gamer_id = db.Column(db.Integer, db.ForeignKey('gamer.id'), nullable=False)
    team_code = db.Column(db.String(10), db.ForeignKey('team.team_code'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    hour_of_day = db.Column(db.Integer, nullable=False)
    is_available = db.Column(db.Boolean, nullable=False)
    gamer = db.relationship('Gamer', backref=db.backref('availability_entries', lazy=True))
    team = db.relationship('Team', backref=db.backref('availability_entries', lazy=True))
    
class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')
    
    def validate_user_username(self, username):
        existing_user_username = Gamer.query.filter_by(
            username=username.data).first()
        
        if existing_user_username:
            raise ValidationError(
                "Username already exists. Please choose a new one."
            )
            
class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')

with app.app_context():
    db.create_all()


#ROUTES
@app.route('/')
def home():
    return render_template('home.html')

#Offers login prompt and hashes password   
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Gamer.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('team_control'))
        flash("There was an issue logging in. Please Try again.")
    return render_template('login.html', form=form)

#Offers a register prompt and decrypts the hash
@app.route('/register' , methods=['GET' , 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf8')
        new_user = Gamer(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))        
    return render_template('register.html', form=form)
    
#logs out to login screen
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/team', methods = ['POST', 'GET'])
@login_required
def team_control():
    print(request.form)
    if "team_code" in request.form:
        team_code = request.form.get("team_code")
        team = Team.query.filter_by(team_code=team_code).first()
        
        if team:
            if team.number_of_members <= 6 and not TeamMember.query.filter_by(gamer_id=current_user.id, team_code=team.team_code).first():
                team_member = TeamMember(gamer_id=current_user.id, team_code=team.team_code)
                db.session.add(team_member)
                team.number_of_members += 1
                db.session.commit()
                update_availabilities(current_user.id, team_code)
                return redirect(url_for("gamer_team", team_code=team_code))
            elif team.number_of_members >= 6:
                flash("Team at maximum capacity.")
                return redirect(url_for('team_control'))
            elif team and TeamMember.query.filter_by(gamer_id=current_user.id, team_code=team.team_code).first():
                return redirect(url_for("gamer_team", team_code=team_code))
        elif not team: 
            flash("No team found.")
            return redirect(url_for('team_control'))
        
    elif "team_name" in request.form:
        team_name = request.form.get("team_name")
        team_code = generate_team_code()
        
        new_team = Team(team_code=team_code, team_name=team_name, number_of_members=1)
        db.session.add(new_team)
        team_member = TeamMember(gamer_id=current_user.id, team_code=new_team.team_code)
        db.session.add(team_member)
        db.session.commit()  
        update_availabilities(current_user.id, team_code)

        return redirect(url_for('gamer_team', team_code=team_code))                
    
    return render_template (
        "team_control.html"
    )

@app.route('/calendar/<team_code>', methods=['POST', 'GET'])
@login_required
def gamer_team(team_code):
    
    team = Team.query.filter_by(team_code=team_code).first()
    team_members = TeamMember.query.filter_by(team_code=team.team_code).all()
    gamer_names = (db.session.query(Gamer.username).join(TeamMember, Gamer.id == TeamMember.gamer_id).filter_by(team_code=team.team_code).all())
    gamer_ids = [member.gamer_id for member in team_members]
    team_name = team.team_name
    
    availabilities = get_users_availabilities_dict(gamer_ids, team.team_code)
    
    if request.method == 'POST':
        start_time = int(request.form['start-time'])
        stop_time = int(request.form['stop-time'])
        day = int(request.form['day'])


        if request.form.get('add-availability'):
            print("INSIDE ADD")
            for hour in range(start_time, stop_time):
                availability = Availability.query.filter_by(gamer_id=current_user.id, team_code=team.team_code, day_of_week=day, hour_of_day=hour).first()
                availability.is_available = True
                db.session.add(availability)
                db.session.commit()
                
        elif request.form.get('remove-availability'):
            for hour in range(start_time, stop_time):
                availability = Availability.query.filter_by(gamer_id=current_user.id, team_code=team.team_code, day_of_week=day, hour_of_day=hour).first()
                availability.is_available = False
                db.session.add(availability)
                db.session.commit()
                
        return redirect(url_for('gamer_team', team_code=team_code))
            
    return render_template(
        "calendar_schedule_table.html",
        team=team,
        gamer_names=gamer_names,
        gamer_ids=gamer_ids,
        curr_user=current_user,
        enumerate=enumerate,
        str=str,
        availabilities=availabilities,
        team_name=team_name,
        team_code=team_code
    )
        
def generate_team_code():
    code_flag = True
    while code_flag:
        team_code = ''.join(random.choices(characters, k=code_length))
        if Team.query.filter_by(team_code=team_code).first():
            code_flag = True
        else:
            code_flag = False
                
    return team_code

def get_users_availabilities_dict(gamer_ids, team_code):
    availability_dict = {}

    for gamer_id in gamer_ids:
        availability_dict[gamer_id] = {}
        for day in range(1, 8):
            availability_dict[gamer_id][day] = {}
            for hour in range(0, 24):
                availability = Availability.query.filter_by(gamer_id=gamer_id, team_code=team_code, day_of_week=day, hour_of_day=hour).first()
                availability_dict[gamer_id][day][hour] = availability.is_available

    return availability_dict

def update_availabilities(gamer_id, team_code):
    for day in range (1, 8):
        for hour in range(0, 24):
            availability = Availability(gamer_id=gamer_id, team_code=team_code, day_of_week=day, hour_of_day=hour, is_available=False)
            db.session.add(availability)
            db.session.commit()
    
app.run(debug=True)