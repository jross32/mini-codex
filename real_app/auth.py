from models import User

def login_required(func):
    def wrapper(*args, **kwargs):
        # Check if user is logged in
        return func(*args, **kwargs)
    return wrapper

def authenticate(username, password):
    user = User.query.filter_by(username=username).first()
    return user and user.check_password(password)
