"""
    User classes & helpers
    ~~~~~~~~~~~~~~~~~~~~~~
"""
import os
import sqlite3
import binascii
import hashlib
from functools import wraps

from flask import current_app
from flask_login import current_user



class UserManager(object):
    """A very simple user Manager, that saves it's data in a SQLite database"""
    def __init__(self):
        pass

    def add_user(self, name, password,
                 active=True, roles="", authentication_method=None):
        conn = sqlite3.connect('Database/database.db')
        cursor = conn.cursor()
        cursor.execute("select * from Users where username  = ?", (name,))
        user = cursor.fetchall()
        if user:
            return False
        if authentication_method is None:
            authentication_method = get_default_authentication_method()
        new_user = {
            'active': active,
            'roles': roles,
            'authentication_method': authentication_method,
            'authenticated': False
        }
        # Currently we have only two authentication_methods: cleartext and
        # hash. If we get more authentication_methods, we will need to go to a
        # strategy object pattern that operates on User.data.
        if authentication_method == 'hash':
            new_user['hash'] = make_salted_hash(password)
        elif authentication_method == 'cleartext':
            new_user['password'] = password
        else:
            raise NotImplementedError(authentication_method)
        cursor.execute("INSERT INTO Users (username,active,authentication_method,password,authenticated,roles) "
                       "VALUES (?,?,?,?,?,?)",
                       (name, new_user['active'], new_user['authentication_method'],
                        new_user['password'],new_user['authenticated'], new_user['roles']))
        conn.commit()
        cursor.execute("SELECT * FROM Users WHERE username  = ?", (name,))
        userdata = cursor.fetchone()
        userdata = {'active': userdata[1], 'authentication_method': userdata[2], 'password': userdata[3],
                    'authenticated': userdata[4], 'roles': userdata[5], 'email': userdata[6], 'featured': userdata[7]}
        conn.close()
        return User(self, name, userdata)

    def get_user(self, name):
        conn = sqlite3.connect('Database/database.db')
        cursor = conn.cursor()
        cursor.execute("select * from Users where username  = ?", (name,))
        userdata = cursor.fetchone()
        conn.close()
        if not userdata:
            return None
        userdata = {'active': userdata[1], 'authentication_method': userdata[2], 'password': userdata[3],
                    'authenticated': userdata[4], 'roles': userdata[5], 'email': userdata[6], 'featured': userdata[7]}
        return User(self, name, userdata)

    def delete_user(self, name):
        conn = sqlite3.connect('Database/database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE username = ?", (name,))
        userdata = cursor.fetchone()
        if not userdata:
            return False
        cursor.execute("DELETE FROM Users WHERE username = ?", (name,))
        conn.commit()
        conn.close()
        return True

    def update(self, name, userdata):
        conn = sqlite3.connect('Database/database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE Users SET active = ?,authentication_method = ?,password = ?,"
                       "authenticated = ?,roles = ?,email = ?, featured = ? where username = ?",
                       (userdata['active'],  userdata['authentication_method'],
                        userdata['password'], userdata['authenticated'], userdata['roles'],
                        userdata['email'], userdata['featured'], name))
        conn.commit()
        conn.close()

    def opt_in(self, name, email):
        conn = sqlite3.connect('Database/database.db')
        cursor = conn.cursor()
        if current_user.opt_in() == 0:
            cursor.execute("UPDATE Users SET email = ?, featured = ? where username = ?", (email, 1, name))
        else:
            cursor.execute("UPDATE Users SET email = ?, featured = ? where username = ?", (email, 0, name))
        conn.commit()
        conn.close()


class User(object):
    def __init__(self, manager, name, data):
        self.manager = manager
        self.name = name
        self.data = data

    def get(self, option):
        return self.data.get(option)

    def set(self, option, value):
        self.data[option] = value
        self.save()

    def save(self):
        self.manager.update(self.name, self.data)

    def is_authenticated(self):
        return self.data.get('authenticated')

    def is_active(self):
        return self.data.get('active')

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.name

    def opt_in(self):
        return self.data.get('featured')

    def get_email(self):
        return self.data.get('email')

    def check_password(self, password):
        """Return True, return False, or raise NotImplementedError if the
        authentication_method is missing or unknown."""
        authentication_method = self.data.get('authentication_method', None)
        if authentication_method is None:
            authentication_method = get_default_authentication_method()
        # See comment in UserManager.add_user about authentication_method.
        if authentication_method == 'hash':
            result = check_hashed_password(password, self.get('hash'))
        elif authentication_method == 'cleartext':
            result = (self.get('password') == password)
        else:
            raise NotImplementedError(authentication_method)
        return result


def get_default_authentication_method():
    return current_app.config.get('DEFAULT_AUTHENTICATION_METHOD', 'cleartext')


def make_salted_hash(password, salt=None):
    if not salt:
        salt = os.urandom(64)
    d = hashlib.sha512()
    d.update(salt[:32])
    d.update(password)
    d.update(salt[32:])
    return binascii.hexlify(salt) + d.hexdigest()


def check_hashed_password(password, salted_hash):
    salt = binascii.unhexlify(salted_hash[:128])
    return make_salted_hash(password, salt) == salted_hash


def protect(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_app.config.get('PRIVATE') and not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        return f(*args, **kwargs)
    return wrapper
