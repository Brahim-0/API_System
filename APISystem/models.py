from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from datetime import timedelta
import jwt
from itsdangerous import Serializer
from APISystem import db, login_manager, app
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)

    def get_reset_token(self, expires_sec=1800):
        encoded_jwt = jwt.encode(
            {'user_id': self.id,
             "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=expires_sec)},
            app.config['SECRET_KEY'], algorithm="HS256")
        return encoded_jwt

    @staticmethod
    def verify_reset_token(token):
        try:
            dict = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return None
        user_id = dict['user_id']
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Key(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    token = db.Column(db.String(130), nullable=False, unique=True)
    expire_date = db.Column(DateTime, default=datetime.utcnow() + timedelta(days=app.config['Subscription_duration']), nullable=False)
    user_email = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=False)
    subscription = db.Column(db.String, nullable=False)  # free   premium-data    premium-requests

    def __repr__(self):
        return f"Key('{self.id}', '{self.expire_date}')"


class DataKey(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    token = db.Column(db.String(130), db.ForeignKey('key.token'), nullable=False, unique=True, )
    data = db.Column(db.FLOAT, default=20.0, nullable=False, )
    consumed = db.Column(db.FLOAT, default=0.0, nullable=False, )


class RequestsKey(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    token = db.Column(db.String(130), db.ForeignKey('key.token'), nullable=False, unique=True)
    requests = db.Column(db.Integer, default=20, nullable=False)
    consumed = db.Column(db.Integer, default=0, nullable=False)
