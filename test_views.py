"""UpWord views tests."""

# run these tests like:
#
#  or: python -m unittest test_views.py

from app import app
import os
from unittest import TestCase

from models import db, connect_db, User, Favorite

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
    
# Don't have WTForms use CSRF at all, since it's a pain to test
# app.config['WTF_CSRF_ENABLED'] = True

class UpWordViewsTestCase(TestCase):
    """Test views of app"""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.drop_all()
            db.create_all()

            u = User.signup(username="testing88", password="testing99", email="testing99@test.com")
            u.id = 9876
            db.session.add(u)
            db.session.commit()
            
            f = Favorite(user_id=9876,book_code=1,book='Genesis',chapter=1,
                         verse=1,num_of_verses=1,text='In the beginning.',translation='ESV')
            f.id = 99
            db.session.add(f)
            db.session.commit()            
            
            self.u = User.query.get(u.id)
            self.f = Favorite.query.get(f.id)
            
            self.client = app.test_client()

    def test_no_user(self):
        """Test navbar to make sure correct links are displayed when no one is logged in"""

        resp = self.client.get("/game")

        # Make sure it redirects
        # self.assertEqual(resp.status_code, 302)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Sign up', str(resp.data))
            
    def test_user_navbar(self):
        """Test navbar to make sure username and 'logout' is displayed when logged in"""

        with self.client as c:
            with c.session_transaction() as sesh:
                sesh['username'] = self.u.username

            resp = c.get("/game")

            self.assertEqual(resp.status_code, 200)
            self.assertIn('testing88', str(resp.data))
            self.assertIn('logout', str(resp.data))

    def test_favorites(self):
        """Test to view users favorites"""
        
        with self.client as c:
            with c.session_transaction() as sesh:
                sesh['username'] = self.u.username

            resp = c.get("/favorites")

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Genesis', str(resp.data))
            self.assertIn('Add', str(resp.data))        
            
    def test_unauthorized_favorites(self):
        """Test viewing favorites while not logged in. Should redirect to 'login' page"""
        
        resp = self.client.get("/favorites")
        
        # check to see if it redirects
        self.assertEqual(resp.status_code, 302)
        self.assertIn('login', str(resp.data))

    def test_game_view(self):
        """Test game view route"""
        
        resp = self.client.get("/game")
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn('game instructions', str(resp.data))
        
    def test_compare_view(self):
        """Test comparison of two translations view route"""
        
        resp = self.client.get("/compare")
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Compare two translations!', str(resp.data))
    
    def test_user_details(self):
        """Test link to display/edit user details is working"""
        
        with self.client as c:
            with c.session_transaction() as sesh:
                sesh['username'] = self.u.username

            resp = c.get("/account")

            self.assertEqual(resp.status_code, 200)
            self.assertIn('testing99@test.com', str(resp.data))
            self.assertIn('Save', str(resp.data))       
            
    def test_logout_user(self):
        """Test to confirm that user is logged out"""
        with self.client as c:
            with c.session_transaction() as sesh:
                sesh['username'] = self.u.username
                
            resp = c.get("/logout")
            # check for redirect to login page
            self.assertEqual(resp.status_code, 302)
            self.assertIn('login', str(resp.data))
            
    def test_favorties_redirect(self):
        """Test if user can add a section of veres to favorites"""
        with app.test_client() as client:
            with client.session_transaction() as sesh:
                sesh['username'] = self.u.username 
                           
            resp = client.post('/add-section',
                               data={'book': '1', 'chapter': '1', 'translation': 'MSG',
                                     'verse1': '1', 'verse2': '2'})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 302)
            self.assertIn(resp.location, '/favorites')

    def test_favorties_follow_redirect(self):
        """Test if user can add a section of veres to favorites"""
        with app.test_client() as client:
            with client.session_transaction() as sesh:
                sesh['username'] = self.u.username 
                           
            resp = client.post('/add-section',
                               data={'book': '1', 'chapter': '1', 'translation': 'MSG',
                                     'verse1': '1', 'verse2': '2'}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('In the beginning', html)
