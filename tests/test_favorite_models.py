"""UpWord Favorite model tests."""

# run these tests like:
#
# python -m unittest test_favorite_models.py


from app import app
# import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Favorite

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

# os.environ['DATABASE_URL'] = "postgresql:///upword-test"
# Use test db and don't clutter tests with SQL
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///upword-test"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['TESTING'] = True

# Now we can import app
# Create our tables 
with app.app_context():
    db.drop_all()
    db.create_all()

class FavoriteModelTestCase(TestCase):
    def setUp(self):
        """Create test client and favorite verse"""
        with app.app_context():
            db.drop_all()
            db.create_all()

            u = User.signup(username="testing88", password="testing99", email="testing99@test.com")
            u.id = 9876
            db.session.add(u)
            db.session.commit()
            
            f = Favorite(user_id=9876,book_code=1,book='book',chapter=1,
                         verse=1,num_of_verses=1,text='text',translation='ESV')
            f.id = 99
            db.session.add(f)
            db.session.commit()            
            
            self.u = User.query.get(u.id)
            self.f = Favorite.query.get(f.id)
            
            self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            res = super().tearDown()
            db.session.rollback()
            return res
        
    def test_fave_model(self):
        """Does basic favorite model work?"""
        with app.app_context():
            f = Favorite(user_id=9876,book_code=2,book='book',chapter=2,
                         verse=2,num_of_verses=1,text='text',translation='ESV')
            f.id = 88
            db.session.add(f)
            db.session.commit()

            # favorite should be in db
            self.assertEqual(f.id, 88)
            self.assertEqual(f.book, "book")
            self.assertEqual(f.translation, 'ESV')
            
    def test_invalid_favorite_added(self):
        """Does favorite fail with invalid input"""
        with app.app_context():
            f = Favorite(user_id=9876,book_code=None,book='book',chapter=2,
                         verse=2,num_of_verses=1,text='text',translation='ESV')

            with self.assertRaises(exc.IntegrityError) as context:
                db.session.add(f)
                db.session.commit()
                
    def test_user_fave_relationship(self):
        """Does relationship between favortie and user work"""
        with app.app_context():
            f  = Favorite.query.get(self.f.id)
            self.assertEqual(self.u.id, f.user.id)
            
    def test_delete_fave(self):
        """Delete favorite from db"""
        with app.app_context():
            db.session.delete(self.f)
            db.session.commit()
            f = Favorite.query.filter_by(id=self.f.id).one_or_none()
            
            self.assertEqual(None, f)
        