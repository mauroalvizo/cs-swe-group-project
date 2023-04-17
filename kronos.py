from flask import *
from dotenv import load_dotenv, find_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

load_dotenv(find_dotenv())

app = Flask(__name__)
db = SQLAlchemy(app)

bcrypt = Bcrypt(app)
#app.config['SQLALCHEMY_DATABASE_URI'] =
#app.config['SECRET_KEY'] = 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    return Gamer.query.get(int(id))


#DATABASE MODELS

class Gamer(db.Model, UserMixin):
    __tablename__ = "gamer"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    
    def is_active(self):
        return True
    
class Group(db.Model):
    __tablename__ = "group"
    
    id = db.Column(db.Integer, primary_key=True) 
    group_code = db.Column(db.String(10), nullable=False, unique=True)
    group_name = db.Column(db.String(80), nullable=False)
    number_of_members = db.Column(db.Integer, nullable=False)
    
class GroupMember(db.Model):
    gamer_id = db.Column(db.Integer, db.ForeignKey('gamer.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), primary_key=True)
    gamer = db.relationship('Gamer', backref=db.backref('group_members', lazy=True))
    group = db.relationship('Group', backref=db.backref('group_members', lazy=True))
    gamer_color = db.Column(db.String(), nullable=False)
    
class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gamer_id = db.Column(db.Integer, db.ForeignKey('gamer.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    hour_of_day = db.Column(db.Integer, nullable=False)
    is_available = db.Column(db.Boolean, nullable=False)
    gamer = db.relationship('Gamer', backref=db.backref('availability_entries', lazy=True))
    group = db.relationship('Group', backref=db.backref('availability_entries', lazy=True))
    
class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_user_username(self, username):
        existing_user_username = Gamer.query.filter_by(
            username=username.data)
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
@app.route('/', methods = ['POST', 'GET'])
def landing():
    return render_template('landing.html')
    
@app.route('/login')
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Gamer.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')
    
    
@app.route('/register' , methods=['GET' , 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = Gamer(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)
    
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))    

@app.route('/group', methods = ['POST', 'GET'])
def enter_code():
    if request.method == 'POST':
        if "Join" in request.form.values():
            group_code = request.form.get("group_code")
            group = Group.query.filter_by(group_code=group_code)
            
            if group:
                if group.number_of_members <= 6 and not GroupMember.query.filter_by(gamer_id=current_user.gamer_id, group_id=group.group_id).first():
                    group_member = GroupMember(gamer_id=current_user.gamer_id, group_id=group.group_id)
                    db.session.add(group_member)
                    db.session.commit()
                    return redirect(url_for("gamer_group", group_code=group_code))
                elif group.number_of_members == 6:
                    flash("Group at maximum capacity.")
                    return redirect(url_for('enter_code'))
            elif group and GroupMember.query.filter_by(gamer_id=current_user.gamer_id, group_id=group.group_id).first():
                return redirect(url_for("gamer_group", group_code=group_code))
            elif not group: 
                flash("No group found.")
                return redirect(url_for('enter_code'))
    
    return render_template (
        "group_control.html"
    )

@app.route('/group/<group_code>', methods = ['POST', 'GET'])
def gamer_group(group_code):
    group_code = request.args.get('group_code')
    group = Group.query.filter_by(group_code=group_code)
    
    group_members = GroupMember.query.filter_by(group_id=group.group_id).all()
    gamer_ids = [member.gamer_id for member in group_members]
    
    return render_template(
        "calendar_schedule_table.html",
        group = group,
        gamer_ids = gamer_ids,
        curr_user = current_user,
        ) 
    
if __name__ == '__main__':
    app.run(debug=True)
    
#app.run(debug=True)