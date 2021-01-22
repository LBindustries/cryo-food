from flask import Flask, url_for, redirect, request, abort
from flask_sqlalchemy import SQLAlchemy
import werkzeug.middleware.proxy_fix
import datetime
import bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "testing"
db = SQLAlchemy(app)
reverse_proxy_app = werkzeug.middleware.proxy_fix.ProxyFix(app=app, x_for=1, x_proto=0, x_host=1, x_port=0, x_prefix=0)
paymentSessions = []


class User(db.Model):
    __tablename__ = "user"
    username = db.Column(db.String, primary_key=True)
    password = db.Column(db.LargeBinary, nullable=False)

    def toJson(self):
        return {'username': self.username}


class Food(db.Model):
    __tablename__ = "food"
    fid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=True)
    date = db.Column(db.DateTime, default=datetime.datetime.today())

    def toJson(self):
        return {'fid': self.fid, 'name': self.name, 'category': self.category, 'date': self.date}


def login(username, password):
    user = User.query.filter_by(username=username).first()
    try:
        return bcrypt.checkpw(bytes(password, encoding="utf-8"), user.password)
    except AttributeError:
        # If no user
        return False


# As of now, this system is not configured to be used with cookies.
# This has been done in accordance with client requests.

@app.route("/")
def page_root():
    return "This server does not serve webpages. Use proper API calls."


@app.route("/checkUser", methods=['GET', 'POST'])
def page_check_user():
    if request.method == "GET":
        return "Use this to verify user credentials. <br>" \
               "Send as params of a POST request [username] and [password]. <br>" \
               "Returns {status: 'success'} upon successful login."
    if login(request.form.get('username'), request.form.get('password')):
        return {'status': 'success'}
    return {'status': 'failure'}


@app.route("/getFood", methods=['GET', 'POST'])
def page_get_food():
    if request.method == "GET":
        return "Use this to get the frozen food data. <br>" \
               "Send as params of a POST request [username] and [password]. <br>" \
               "Returns {status: 'success', content:[fid: 1, foodName:'lasagna', category:'pasta', date:'YYYY-MM-DD hh:mm]}"
    if login(request.form.get('username'), request.form.get('password')):
        food = Food.query.all()
        return {'status': 'success', 'content': [a.toJson for a in food]}
    return {'status': 'failure'}


@app.route("/addFood", methods=['GET', 'POST'])
def page_add_food():
    if request.method == "GET":
        return "Use this to add food to the fridge. <br>" \
               "Send as params of a POST request [username], [password], [food-name], [food-category]. <br>" \
               "Returns {status: 'success'}"
    if login(request.form.get('username'), request.form.get('password')):
        db.session.add(Food(name=request.form.get('food-name'), category=request.form.get('food-category')))
        db.session.commit()
        return {'status': 'success'}
    return {'status': 'failure'}


@app.route("/remFood", methods=['GET', 'POST'])
def page_remove_food():
    if request.method == "GET":
        return "Use this to remove food to the fridge. <br>" \
               "Send as params of a POST request [username], [password], [fid]. <br>" \
               "Returns {status: 'success'}"
    if login(request.form.get('username'), request.form.get('password')):
        food = Food.query.get_or_404(request.form.get('fid'))
        db.session.delete(food)
        db.session.commit()
        return {'status': 'success'}
    return {'status': 'failure'}


@app.route("/getUsers", methods=['GET', 'POST'])
def page_get_users():
    if request.method == "GET":
        return "Use this to get the users data. <br>" \
               "Send as params of a POST request [username] and [password]. <br>" \
               "Returns {status: 'success', content:[username:'pippo']}"
    if login(request.form.get('username'), request.form.get('password')):
        users = User.query.all()
        return {'status': 'success', 'content': [a.toJson for a in users]}
    return {'status': 'failure'}


@app.route("/changePw", methods=['GET', 'POST'])
def page_change_password():
    if request.method == "GET":
        return "Use this to change an user password. <br>" \
               "Send as params of a POST request [username], [password], [user-username], [user-password]. <br>" \
               "Returns {status: 'success'}"
    if login(request.form.get('username'), request.form.get('password')):
        user = User.query.get_or_404(request.form.get('user-username'))
        p = bytes(request.form.get('user-password'), encoding="utf-8")
        ash = bcrypt.hashpw(p, bcrypt.gensalt())
        user.password = ash
        db.session.commit()
        return {'status': 'success'}
    return {'status': 'failure'}


@app.route("/addUser", methods=['GET', 'POST'])
def page_add_user():
    if request.method == "GET":
        return "Use this to create a new user. <br>" \
               "Send as params of a POST request [username], [password], [user-username], [user-password]. <br>" \
               "Returns {status: 'success'}"
    if login(request.form.get('username'), request.form.get('password')):
        p = bytes(request.form.get('user-password'), encoding="utf-8")
        ash = bcrypt.hashpw(p, bcrypt.gensalt())
        db.session.add(User(username=request.form.get('user-username'), password=ash))
        db.session.commit()
        return {'status': 'success'}
    return {'status': 'failure'}


@app.route("/delUser", methods=['GET', 'POST'])
def page_rem_user():
    if request.method == "GET":
        return "Use this to delete a user. <br>" \
               "Send as params of a POST request [username], [password], [target-username]. <br>" \
               "Returns {status: 'success'}"
    if login(request.form.get('username'), request.form.get('password')) and not request.form.get(
            'username') == request.form.get('target-username'):
        user = User.query.get_or_404(request.form.get('user-username'))
        db.session.delete(user)
        db.session.commit()
        return {'status': 'success'}
    return {'status': 'failure'}


if __name__ == "__main__":
    print("Starting the cryo-food server...")
    db.create_all()
    user = User.query.all()
    if len(user) == 0:
        p = bytes("admin", encoding="utf-8")
        ash = bcrypt.hashpw(p, bcrypt.gensalt())
        db.session.add(User(username="admin", password=ash))
        db.session.commit()
    print("Startup complete, now serving on the choosen port.")
    app.run(debug=True, host="0.0.0.0")
