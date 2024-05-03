"""Models for UpWord app."""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
db = SQLAlchemy()

def connect_db(app):
    """ Connect to database """
    with app.app_context():
        db.app = app
        db.init_app(app)
        db.create_all()

class User(db.Model):
    """ User class """
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer,
                   primary_key=True,
                   autoincrement=True)

    username = db.Column(db.Text,
                         nullable=False,
                         unique=True,)

    password = db.Column(db.Text,
                         nullable=False)
    
    email = db.Column(db.Text,
                      nullable=False,
                      unique=True)
    
    first_name = db.Column(db.Text)

    last_name = db.Column(db.Text)        
        
    fav_translation = db.Column(db.Text,
                         default='ESV')    
    
    favorites = db.relationship('Favorite', backref='user', cascade='all, delete')
    
    def __repr__(self):
        return f'<User #{self.id}: {self.username}>'
    
    @classmethod
    def signup(cls, username, password, email):
        """ Hash password and add user to db """
        
        hashed_pw = bcrypt.generate_password_hash(password).decode('UTF-8')
        
        user = User(username=username, password=hashed_pw, email=email)
        
        db.session.add(user)
        return user
    
    @classmethod
    def login(cls, username, password):
        """ Authenticate user login credentials and return user or False """
        
        user = cls.query.filter_by(username=username).first()
        
        if user:
            auth = bcrypt.check_password_hash(user.password, password)
            if auth:
                return user
        
        return False
    
class Favorite(db.Model):
    """ Favorite verses class """
    
    __tablename__ = 'favorites'
    
    
    id = db.Column(db.Integer,
                   primary_key=True,
                   autoincrement=True)
    
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete='cascade'),
                        nullable=False)
        
    book_code = db.Column(db.Integer,
                     nullable=False)
    
    book = db.Column(db.Text,
                     nullable=False)

    chapter = db.Column(db.Integer,
                        nullable=False)

    verse = db.Column(db.Integer,
                      nullable=False)

    num_of_verses = db.Column(db.Integer,
                          nullable=False)
    
    text = db.Column(db.Text,
                     nullable=False)

    translation = db.Column(db.Text,
                            nullable=False)
    
    def __repr__(self):
        return f'<user #{self.user_id} {self.book} {self.chapter}>'
    