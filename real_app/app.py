from flask import Flask
from auth import login_required
from models import User

app = Flask(__name__)

@app.route('/')
@login_required
def home():
    return 'Hello'

if __name__ == '__main__':
    app.run()
