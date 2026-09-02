from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from flask_cors import CORS
from flask_login import ( LoginManager, UserMixin, login_user, logout_user, login_required, current_user )
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

frontend_url = os.getenv(
    'FRONTEND_URL',
    'http://localhost:3000'
)

CORS(
    app,
    resources={r"/*": {"origins": frontend_url}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

class UserType(Enum):
    Admin = 'Admin'
    User = 'User'

# Render db configuration as db
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Flask login manager
login_manager = LoginManager() 
login_manager.init_app(app)

@login_manager.user_loader 
def load_user(userid): 
    return db.session.get(User, int(userid)) 

# Login required to access information
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.usertype != UserType.Admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)

    return decorated_function

# Registration always defaults to the User role
@app.route('/register', methods=['POST']) 
def register(): 
    data = request.get_json() 
    email = data.get('email') 
    password = data.get('password') 
    if not email or not password: 
        return jsonify({ 'error': 'Email and password are required' }), 400 # Check if email already exists 
    existing_user = User.query.filter_by(email=email).first() 
    if existing_user: 
        return jsonify({ 'error': 'Email already registered' }), 409 # Create normal user 
    user = User( 
        email=email, 
        phone=data.get('phone'), 
        address=data.get('address'), 
        password=generate_password_hash(password), 
        usertype=UserType.User ) 
    db.session.add(user) 
    db.session.commit() 
    return jsonify({ 
        'message': 'Account created successfully', 
        'userid': user.userid,
        'usertype': user.usertype.value if isinstance(user.usertype, UserType) else user.usertype
        }), 201


@app.route('/login', methods=['POST']) 
def login():
    data = request.get_json() 
    email = data.get('email') 
    password = data.get('password') 
    user = User.query.filter_by(email=email).first() 
    if not user or not check_password_hash(user.password, password): 
        return jsonify({ 
            'error': 'Invalid email or password' 
            }), 401 
    login_user(user) 
    return jsonify({ 
        'message': 'Login successful', 
        'userid': user.userid, 
        'email': user.email, 
        'usertype': user.usertype.value if isinstance(user.usertype, UserType) else user.usertype
        }), 200

@app.route('/logout', methods=['POST']) 
@login_required 
def logout(): 
    logout_user() 
    return jsonify({ 
        'message': 'Logged out successfully' 
        })

@app.route('/skills', methods=['POST'])
def create_skill():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Skill name is required'}), 400

    skill = Skill(name=name)

    db.session.add(skill)
    db.session.commit()

    return jsonify({
        'skillid': skill.skillid,
        'name': skill.name
    }), 201


@app.route('/applications', methods=['POST'])
def create_application():
    data = request.get_json()
    posting_id = data.get('postingid')
    user_id = data.get('userid')
    if not posting_id or not user_id:
        return jsonify({ 'error': 'postingid and userid are required' }), 400
    posting = db.session.get(Posting, posting_id)
    if not posting:
        return jsonify({ 'error': 'Posting not found' }), 404

    existing_application = Application.query.filter_by(
        postingid=posting_id,
        userid=user_id
    ).first()
    if existing_application:
        return jsonify({ 'error': 'You have already applied to this posting' }), 409

    application = Application(
        postingid=posting_id,
        userid=user_id
    )

    db.session.add(application)
    db.session.commit()

    return jsonify({
        'message': 'Application created successfully',
        'postingid': application.postingid,
        'userid': application.userid,
        'status': application.status
    }), 201

@app.route('/users/<int:userid>/role', methods=['PUT'])
def update_user_role(userid):
    data = request.get_json()
    if not data or 'usertype' not in data:
        return jsonify({'error': 'usertype is required'}), 400

    new_usertype_str = data.get('usertype')

    try:
        new_usertype = UserType[new_usertype_str]
    except KeyError:
        return jsonify({
            'error': f'Invalid usertype. Must be one of: User, Admin'
        }), 400

    user = db.session.get(User, userid)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.usertype = new_usertype
    db.session.commit()

    return jsonify({
        'message': 'User type updated successfully',
        'userid': user.userid,
        'usertype': user.usertype.value if isinstance(user.usertype, UserType) else user.usertype
    }), 200

@app.route('/me') 
def get_current_user(): 
    if not current_user.is_authenticated: 
        return jsonify({ 'logged_in': False }) 
    return jsonify({ 'logged_in': True, 'userid': current_user.userid, 'email': current_user.email, 'usertype': current_user.usertype.value if isinstance(current_user.usertype, UserType) else current_user.usertype })

@app.route('/user') 
@login_required 
def user_dashboard(): 
    return jsonify({ 'message': 'Welcome to user dashboard', 'userid': current_user.userid, 'email': current_user.email })


@app.route('/admin') 
@admin_required 
def admin_dashboard(): 
    return jsonify({ 'message': 'Welcome to admin dashboard', 'userid': current_user.userid, 'email': current_user.email })


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    userid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, nullable=False, unique=True)
    phone = db.Column(db.String)
    address = db.Column(db.String)
    password = db.Column(db.String, nullable=False)

    usertype = db.Column(
        db.Enum(UserType, name='usertype', native_enum=False),
        nullable=False,
        default=UserType.User
    )

    def get_id(self):
        return str(self.userid)

class Skill(db.Model):
    __tablename__ = 'skills'

    skillid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)


class UserSkill(db.Model):
    __tablename__ = 'userskills'

    userid = db.Column(db.Integer, db.ForeignKey('users.userid', ondelete='CASCADE'), primary_key=True)
    skillid = db.Column(db.Integer, db.ForeignKey('skills.skillid', ondelete='CASCADE'), primary_key=True)


class Posting(db.Model):
    __tablename__ = 'postings'

    postingid = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String, nullable=False)
    position = db.Column(db.String, nullable=False)


class Application(db.Model):
    __tablename__ = 'applications'

    postingid = db.Column(db.Integer, db.ForeignKey('postings.postingid', ondelete='CASCADE'), primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid', ondelete='CASCADE'), primary_key=True)
    status = db.Column(db.Enum('Applied', 'Interviewing', 'Rejected', 'Accepted', name='application_status'), nullable=False, server_default='Applied')

@app.route('/users')
def get_users():
    users = User.query.all()

    return jsonify([
        {
            'userid': user.userid,
            'email': user.email,
            'phone': user.phone,
            'address': user.address,
            'usertype': user.usertype.value if isinstance(user.usertype, UserType) else user.usertype
        }
        for user in users
    ])

@app.route('/users/<int:userid>/skills')
def get_user_skills(userid):
    user = db.session.get(User, userid)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify([
        {
            'skillid': skill.skillid,
            'name': skill.name
        }
        for skill in user.skills
    ]), 200

@app.route('/postings')
def get_postings():
    postings = Posting.query.all()

    return jsonify([
        {
            'postingid': posting.postingid,
            'company': posting.company,
            'position': posting.position
        }
        for posting in postings
    ])

@app.route('/postings/not-applied/<int:userid>')
def get_postings_not_applied(userid):
    applied_postings = db.session.query(Application.postingid).filter(Application.userid == userid)

    postings = Posting.query.filter(~Posting.postingid.in_(applied_postings)).all()

    return jsonify([
        {
            'postingid': posting.postingid,
            'company': posting.company,
            'position': posting.position
        }
        for posting in postings
    ])

@app.route('/applications/users/<int:userid>')
def get_applications(userid):
    applications = Application.query.filter_by(userid=userid).all()

    return jsonify([
        {
            'postingid': app.postingid,
            'userid': app.userid,
            'status': app.status
        }
        for app in applications
    ])


@app.route('/applications')
def get_all_applications():
    applications = Application.query.all()

    return jsonify([
        {
            'postingid': app.postingid,
            'userid': app.userid,
            'status': app.status
        }
        for app in applications
    ])

@app.route('/skills')
def get_skills():
    skills = Skill.query.all()

    return jsonify([
        {
            'userid': skill.userid,
            'name': skill.name
        }
        for skill in skills
    ])

@app.route('/tables')
def get_tables():
    result = db.session.execute(db.text("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name;
    """))

    return {
        'tables': [
            {
                'schema': row.table_schema,
                'table': row.table_name
            }
            for row in result
        ]
    }

@app.route('/columns/<table_name>')
def get_columns(table_name):
    result = db.session.execute(db.text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = :table_name
        ORDER BY ordinal_position;
    """), {'table_name': table_name})

    return {
        'table': table_name,
        'columns': [
            {
                'name': row.column_name,
                'type': row.data_type
            }
            for row in result
        ]
    }


@app.route('/db-test')
def db_test():
    try:
        db.session.execute(db.text('SELECT 1'))
        return {'status': 'connected'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500


if __name__ == '__main__':
    app.run(debug=True)