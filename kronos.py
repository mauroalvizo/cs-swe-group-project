from flask import *
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
    
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    group_code = db.Column(db.String(10), nullable=False, unique=True)
    group_name = db.Column(db.String(80), nullable=False)
    number_of_members = db.Column(db.Integer, nullable=False)
    
class GroupMember(db.model):
    gamer_id = db.Column(db.Integer, db.ForeignKey('gamer.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), primary_key=True)
    gamer = db.relationship('Gamer', backref=db.backref('group_members', lazy=True))
    group = db.relationship('Group', backref=db.backref('group_members', lazy=True))
    gamer_color = db.Column(db.String(), nullable=False)
    
class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gamer_id = db.Column(db.Integer, db.ForeignKey('Gamer.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    hour_of_day = db.Column(db.Integer, nullable=False)
    is_available = db.Column(db.Boolean, nullable=False)
    gamer = db.relationship('Gamer', backref=db.backref('availability_entries', lazy=True))
    group = db.relationship('Group', backref=db.backref('availability_entries', lazy=True))


with app.app_context():
    db.create_all()




#ROUTES
@app.route('/', methods = ['POST', 'GET'])
def landing():
    if request.method == 'POST':
        if "Login" in request.form.values():
            username = request.form.get("username")
            return redirect(url_for("login", username=username))
    
        if "Register" in request.form.values():
            username = request.form.get("username")
            return redirect(url_for("register", username=username))
    
    return render_template (
        "calendar_schedule_table.html"
    )
    
@app.route('/login')
def login():
    username = request.args.get('username')
    user = Gamer.query.filter_by(username=username).first()
    
    if user:
        login_user(user)
        return redirect(url_for('enter_code'))
    else:
        flash("No user found.")
        return redirect(url_for("landing"))
    
    
@app.route('/register')
def register():
    username = request.args.get('username')
    user = Gamer.query.filter_by(username=username).first()
    
    if user:
        flash("User already exists.")
        return redirect(url_for('home'))
    elif user is None:
        user = Gamer(username=username)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("enter_code"))
    
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("landing"))


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
    
    return render_template (
        "calendar_schedule_table.html",
        group = group,
        gamer_ids = gamer_ids;
        curr_user = current_user,
    ) 
    
app.run(debug=True)