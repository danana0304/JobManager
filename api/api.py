from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from flask_cors import CORS
import time

load_dotenv()

app = Flask(__name__)

CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'

    userid = db.Column(db.Integer, primary_key=True)
    usertype = db.Column(db.Enum('Admin', 'User', name='user_type'), nullable=False, server_default='User')
    email = db.Column(db.String, nullable=False)
    phone = db.Column(db.String)
    address = db.Column(db.String)
    password = db.Column(db.String, nullable=False)


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
            'address': user.address
        }
        for user in users
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


@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()

    user = User(
        email=data['email'],
        phone=data['phone'],
        address=data['address'],
        password=data['password']
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'userid': user.userid,
        'email': user.email,
        'phone': user.phone,
        'address': user.address
    }), 201


@app.route('/postings', methods=['POST'])
def create_posting():
    data = request.get_json()

    posting = Posting(
        company=data['company'],
        position=data['position']
    )

    db.session.add(posting)
    db.session.commit()

    return jsonify({
        'postingid': posting.postingid,
        'company': posting.company,
        'position': posting.position
    }), 201


@app.route('/db-test')
def db_test():
    try:
        db.session.execute(db.text('SELECT 1'))
        return {'status': 'connected'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/time')
def get_current_time():
    import time
    return {'time': time.time()}


if __name__ == '__main__':
    app.run(debug=True)