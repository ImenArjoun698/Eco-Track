from flask import Blueprint

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return "Login page"

@auth.route('/register')
def register():
    return "Register page"
