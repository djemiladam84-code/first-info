from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('opportunity_id', db.Integer, db.ForeignKey('opportunities.id'), primary_key=True),
    db.Column('added_at', db.DateTime, default=datetime.utcnow)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' ou 'admin'
    country = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    favorite_opportunities = db.relationship(
        'Opportunity',
        secondary=favorites,
        backref=db.backref('favorited_by', lazy='dynamic'),
        lazy='dynamic',
        order_by=favorites.c.added_at.desc()
    )
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    # ex: 'Hackathon', 'Bourse', 'Stage', 'Emploi', 'Formation', 'Concours'

    def __repr__(self):
        return f'<Category {self.name}>'




class Opportunity(db.Model):
    __tablename__ = 'opportunities'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    organizer = db.Column(db.String(150))
    link = db.Column(db.String(500), nullable=False)
    country_scope = db.Column(db.String(100))  # ex: 'Benin', 'Afrique', 'International'
    deadline = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected', 'expired'
    source = db.Column(db.String(50), default='manual')   # 'manual' ou 'ai'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    category = db.relationship('Category', backref='opportunities')

    def __repr__(self):
        return f'<Opportunity {self.title}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))