"""UpWord User model tests."""

# run these tests like:
#
# python -m unittest test_user_models.py


from app import app
import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Favorite

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///upword-test"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TESTING'] = True

# Now we can import app

# Create our tables 

with app.app_context():
    db.drop_all()
    db.create_all()

class UserModelTestCase(TestCase):
    """Test model for users."""

    def setUp(self):
        """Create test client."""
        with app.app_context():
            db.drop_all()
            db.create_all()

            u = User.signup(username="testing99", password="testing99", email="testing99@test.com")
            u.id = 9876
            db.session.add(u)
            db.session.commit()

            self.u = User.query.get(u.id)
            
            self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            res = super().tearDown()
            db.session.rollback()
            return res

    def test_user_model(self):
        """Does basic user model work?"""
        with app.app_context():
            u = User(username="testing88", password="HASHED_PASSWORD", email="testing88@test.com")
            u.id = 88
            
            db.session.add(u)
            db.session.commit()

            # user should be in db
            self.assertEqual(u.id, 88)
            self.assertEqual(u.username, "testing88")
            self.assertEqual(u.fav_translation, 'ESV')

    def test_invalid_username_signup(self):
        """Does user signup fail with invalid username"""
        with app.app_context():
            invalid = User.signup(None, "password", "testing88@test.com")
            with self.assertRaises(exc.IntegrityError) as context:
                db.session.add(invalid)
                db.session.commit()
                
    def test_invalid_email_signup(self):
        """Does user signup fail with invalid email"""
        with app.app_context():
            invalid = User.signup('username', "password", None)
            with self.assertRaises(exc.IntegrityError) as context:
                db.session.add(invalid)
                db.session.commit()
                
    def test_invalid_password_signup(self):
        """Does signup fail with invalid password"""
        with app.app_context():
            with self.assertRaises(ValueError) as context:
                User.signup("testtest", None, 'test@test.com')

            with self.assertRaises(ValueError) as context:
                User.signup("testtest", None, 'test@test.com')
    
    def test_password_hasing(self):
        """Does users password get stored as hashed pswd"""
        
        with app.app_context():
            # password should be hashed 
            self.assertNotEqual(self.u.password, "testing99")
            
    def test_valid_login(self):
        """Does valid login authentication work"""
        
        with app.app_context():
            u = User.login(self.u.username, 'testing99')
            
            self.assertIsNotNone(u)
            self.assertEqual(u.id, self.u.id)
    
    def test_user_fave_relationship(self):
        """Test to access users favorites"""
        with app.app_context():
            f = Favorite(user_id=self.u.id,book_code=None,book='book',chapter=2,
                        verse=2,num_of_verses=1,text='text',translation='ESV')
            u = User.query.get(self.u.id)
            
            self.assertIsNotNone(u.favorites)
            
    def test_delete_user(self):
        """Test to delete user and linked favorites relationships"""
        with app.app_context():    
            f = Favorite(user_id=self.u.id,book_code=1,book='book1',chapter=2,
                        verse=3,num_of_verses=1,text='text1',translation='ESV')
            db.session.add(f)
            db.session.commit()
            
            user_id = self.u.id
            db.session.delete(self.u)
            db.session.commit()
            
            faves = Favorite.query.filter_by(user_id=user_id).one_or_none()
            user = User.query.filter_by(id=user_id).one_or_none()
            
            self.assertEqual(None, faves)
            self.assertEqual(None, user)