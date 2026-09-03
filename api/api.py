from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from flask_cors import CORS
from flask_login import ( LoginManager, UserMixin, login_user, logout_user, login_required, current_user )
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum
from prometheus_flask_exporter import PrometheusMetrics

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
metrics = PrometheusMetrics(app)

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

@app.route('/postings', methods=['POST'])
def create_posting():
    data = request.get_json()
    company = data.get('company')
    position = data.get('position')
    description = data.get('description')
    postedby = data.get('postedby')

    if not company or not position:
        return jsonify({'error': 'Company and position are required'}), 400

    posting = Posting(
        company=company,
        position=position,
        description=description,
        postedby=postedby
    )

    db.session.add(posting)
    db.session.commit()

    return jsonify({
        'message': 'Posting created successfully',
        'postingid': posting.postingid,
        'company': posting.company,
        'position': posting.position,
        'description': posting.description,
        'postedby': posting.postedby
    }), 201


@app.route('/audit-logs', methods=['POST'])
def create_audit_log():
    data = request.get_json() or {}

    action = data.get('action')
    entity_type = data.get('entitytype')
    actor_id = data.get('actoruserid')

    # Basic validation matching check constraint
    valid_actions = ['CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT']
    if not action or action not in valid_actions:
        return jsonify({
            'error': f'Invalid or missing action. Must be one of: CREATE, UPDATE, DELETE, LOGIN, LOGOUT'
        }), 400

    if not entity_type:
        return jsonify({'error': 'entitytype is required'}), 400

    try:
        log_entry = AuditLog(
            actoruserid=actor_id,
            action=action,
            entitytype=entity_type,
            entityid=data.get('entityid'),
            oldvalues=data.get('oldvalues'),
            newvalues=data.get('newvalues'),
            ipaddress=request.remote_addr,
            useragent=request.user_agent.string
        )

        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error', 'details': str(e)}), 500

    return jsonify({
        'message': 'Audit log recorded',
        'auditid': log_entry.auditid,
        'action': log_entry.action,
        'entitytype': log_entry.entitytype,
        'actoruserid': log_entry.actoruserid
    }), 201

@app.route('/users/<int:userid>', methods=['PUT'])
def update_user_profile(userid):
    user = db.session.get(User, userid)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}

    if 'email' in data:
        existing_user = User.query.filter(User.email == data['email'], User.userid != userid).first()
        if existing_user:
            return jsonify({'error': 'Email already in use by another user'}), 409
        user.email = data['email']

    if 'phone' in data:
        user.phone = data['phone']

    if 'address' in data:
        user.address = data['address']

    if 'password' in data and data['password']:
        user.password = generate_password_hash(data['password'])

    if 'usertype' in data:
        try:
            user.usertype = UserType[data['usertype']]
        except KeyError:
            return jsonify({
                'error': 'Invalid usertype. Must be one of: User, Admin'
            }), 400

    db.session.commit()

    return jsonify({
        'message': 'User profile updated successfully',
        'userid': user.userid,
        'email': user.email,
        'phone': user.phone,
        'address': user.address,
        'usertype': user.usertype.value if isinstance(user.usertype, UserType) else user.usertype
    }), 200

@app.route('/users/<int:userid>/role', methods=['PUT'])
def update_user_role(userid):
    data = request.get_json() or {}
    if 'usertype' not in data:
        return jsonify({'error': 'usertype is required'}), 400

    try:
        new_usertype = UserType[data['usertype']]
    except (KeyError, TypeError):
        return jsonify({'error': 'Invalid usertype. Must be one of: User, Admin'}), 400

    user = db.session.get(User, userid)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.usertype = new_usertype
    db.session.commit()

    return jsonify({
        'message': 'User type updated successfully',
        'userid': user.userid,
        'usertype': user.usertype.value
    }), 200

@app.route('/applications/postings/<int:postingid>/users/<int:userid>', methods=['PUT'])
def update_application_status(postingid, userid):
    data = request.get_json()

    if not data or 'status' not in data:
        return jsonify({'error': 'status is required'}), 400

    new_status = data.get('status')

    valid_statuses = ['Applied', 'Interviewing', 'Rejected', 'Accepted']
    if new_status not in valid_statuses:
        return jsonify({
            'error': f'Invalid status. Must be one of: Applied, Interviewing, Rejected, Accepted'
        }), 400

    application = Application.query.filter_by(
        postingid=postingid,
        userid=userid
    ).first()

    if not application:
        return jsonify({'error': 'Application not found'}), 404

    application.status = new_status
    db.session.commit()

    return jsonify({
        'message': 'Application status updated successfully',
        'postingid': application.postingid,
        'userid': application.userid,
        'status': application.status
    }), 200

@app.route('/postings/<int:postingid>', methods=['PUT'])
def update_posting(postingid):
    posting = db.session.get(Posting, postingid)
    if not posting:
        return jsonify({'error': 'Posting not found'}), 404

    data = request.get_json() or {}

    if 'company' in data:
        posting.company = data['company']
    if 'position' in data:
        posting.position = data['position']
    if 'description' in data:
        posting.description = data['description']

    db.session.commit()

    return jsonify({
        'message': 'Posting updated successfully',
        'postingid': posting.postingid,
        'company': posting.company,
        'position': posting.position,
        'description': posting.description,
        'postedby': posting.postedby
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



class Posting(db.Model):
    __tablename__ = 'postings'

    postingid = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String, nullable=False)
    position = db.Column(db.String, nullable=False)
    description = db.Column(db.String(1000), nullable=True)
    postedby = db.Column(db.Integer, db.ForeignKey('users.userid', ondelete='SET NULL'), nullable=True)


class Application(db.Model):
    __tablename__ = 'applications'

    postingid = db.Column(db.Integer, db.ForeignKey('postings.postingid', ondelete='CASCADE'), primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid', ondelete='CASCADE'), primary_key=True)
    status = db.Column(db.Enum('Applied', 'Interviewing', 'Rejected', 'Accepted', name='application_status'), nullable=False, server_default='Applied')


class AuditLog(db.Model):
    __tablename__ = 'auditlog'

    auditid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    actoruserid = db.Column(db.Integer, db.ForeignKey('users.userid', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    entitytype = db.Column(db.String(50), nullable=False)
    entityid = db.Column(db.BigInteger, nullable=True)
    oldvalues = db.Column(db.JSON, nullable=True)
    newvalues = db.Column(db.JSON, nullable=True)
    ipaddress = db.Column(db.String(45), nullable=True)
    useragent = db.Column(db.Text, nullable=True)
    createdat = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)

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
    postings = Posting.query.order_by(Posting.postingid.desc()).all()

    return jsonify([
        {
            'postingid': posting.postingid,
            'company': posting.company,
            'position': posting.position,
            'description': posting.description,
            'postedby': posting.postedby
        }
        for posting in postings
    ])

@app.route('/postings/not-applied/<int:userid>')
def get_postings_not_applied(userid):
    applied_postings = db.session.query(Application.postingid).filter(Application.userid == userid)

    postings = (
        Posting.query
        .filter(~Posting.postingid.in_(applied_postings))
        .order_by(Posting.postingid.desc())
        .all()
    )

    return jsonify([
        {
            'postingid': posting.postingid,
            'company': posting.company,
            'position': posting.position,
            'description': posting.description,
            'postedby': posting.postedby
        }
        for posting in postings
    ])

@app.route('/postings/<int:postingid>/applicants')
def get_posting_applicants(postingid):
    posting = db.session.get(Posting, postingid)
    if not posting:
        return jsonify({'error': 'Posting not found'}), 404

    results = (
        db.session.query(Application, User)
        .join(User, Application.userid == User.userid)
        .filter(Application.postingid == postingid)
        .all()
    )

    return jsonify([
        {
            'postingid': app.postingid,
            'status': app.status,
            'user': {
                'userid': user.userid,
                'email': user.email,
                'phone': user.phone,
                'address': user.address
            }
        }
        for app, user in results
    ]), 200

@app.route('/users/<int:userid>/postings')
def get_user_postings(userid):
    # Verify user exists
    user = db.session.get(User, userid)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Query all postings created by this user
    postings = (
        Posting.query
        .filter_by(postedby=userid)
        .order_by(Posting.postingid.desc())
        .all()
    )

    return jsonify([
        {
            'postingid': posting.postingid,
            'company': posting.company,
            'position': posting.position,
            'description': posting.description,
            'postedby': posting.postedby
        }
        for posting in postings
    ]), 200

@app.route('/applications/users/<int:userid>')
def get_applications(userid):
    applications = (
        Application.query
        .filter_by(userid=userid)
        .order_by(
            db.case(
                (Application.status == 'Accepted', 1),
                (Application.status == 'Interviewing', 2),
                (Application.status == 'Applied', 3),
                (Application.status == 'Rejected', 4),
                else_=5
            ),
            Application.postingid.desc()
        )
        .all()
    )

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
    applications = (
        Application.query
        .order_by(
            db.case(
                (Application.status == 'Accepted', 1),
                (Application.status == 'Interviewing', 2),
                (Application.status == 'Applied', 3),
                (Application.status == 'Rejected', 4),
                else_=5
            ),
            Application.postingid.desc()
        )
        .all()
    )

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

@app.route('/audit-logs', methods=['GET'])
def get_audit_logs():
    logs = AuditLog.query.order_by(AuditLog.createdat.desc()).all()

    return jsonify([
        {
            'auditid': log.auditid,
            'actoruserid': log.actoruserid,
            'action': log.action,
            'entitytype': log.entitytype,
            'entityid': log.entityid,
            'oldvalues': log.oldvalues,
            'newvalues': log.newvalues,
            'ipaddress': log.ipaddress,
            'useragent': log.useragent,
            'createdat': log.createdat.isoformat() if log.createdat else None
        }
        for log in logs
    ]), 200

@app.route('/applications/postings/<int:postingid>/users/<int:userid>', methods=['DELETE'])
def delete_application(postingid, userid):
    application = Application.query.filter_by(
        postingid=postingid,
        userid=userid
    ).first()

    if not application:
        return jsonify({'error': 'Application not found'}), 404

    db.session.delete(application)
    db.session.commit()

    return jsonify({'message': 'Application deleted successfully'}), 200

@app.route('/postings/<int:postingid>', methods=['DELETE'])
def delete_posting(postingid):
    posting = db.session.get(Posting, postingid)
    if not posting:
        return jsonify({'error': 'Posting not found'}), 404

    db.session.delete(posting)
    db.session.commit()

    return jsonify({'message': 'Posting deleted successfully'}), 200

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