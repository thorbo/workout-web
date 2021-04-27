import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, json
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date


from helpers import apology, login_required, datatable, addgoal, projectwin

# Configure application
app = Flask(__name__)


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///workout.db")
"""
    DB Structure:
    sqlite3 workout.db;
    CREATE TABLE users(id INTEGER PRIMARY KEY NOT NULL, name TEXT NOT NULL, hash TEXT NOT NULL);
    CREATE TABLE groups(group_num INTEGER PRIMARY KEY NOT NULL, group_name TEXT NOT NULL, type TEXT NOT NULL, goal INTEGER, start DATETIME);
    CREATE TABLE registry(user_id INTEGER, group_num INTEGER, FOREIGN KEY (user_id) REFERENCES users(id), FOREIGN KEY (group_num) REFERENCES groups(group_num));
    CREATE TABLE data (user_id INTEGER, type TEXT NOT NULL, value FLOAT, time DATETIME, FOREIGN KEY (user_id) REFERENCES users(id));

"""

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    user = session["user_id"]

    if request.method == "POST":
        # Update data table with workout data
        action = request.form.get("logbutton")
        if action == "logwork":
            row = db.execute("SELECT * FROM data WHERE (user_id, time, type) = (?, ?, ?)", user, request.form.get("date"), request.form.get("type"))
            if len(row) == 0:
                # New workout being logged
                db.execute("INSERT INTO data VALUES (?, ?, ?, ?)", user, request.form.get("type"), request.form.get("log"), request.form.get("date"))
            else:
                # Overwrite previous workout
                db.execute("UPDATE data SET value = ? WHERE (user_id, type, time) = (?, ?, ?)", request.form.get("log"), user, request.form.get("type"), request.form.get("date"))

        # user selects a group that they want to see
        GROUPS = db.execute("SELECT * FROM groups WHERE group_num IN (SELECT group_num FROM registry WHERE user_id = ?)", user)
        GROUP = next((g for g in GROUPS if g["group_num"] == int(request.form["sel1"])), None)
    else:
        # Request groups that user belongs to
        #TODO - handle when user isn't signed up to any groups
        GROUPS = db.execute("SELECT * FROM groups WHERE group_num IN (SELECT group_num FROM registry WHERE user_id = ?)", user)
        GROUP = GROUPS[0]
    goal = GROUP['goal']
    typ = GROUP['type']
    USERS = db.execute("SELECT user_id, name FROM registry JOIN users ON registry.user_id = users.id WHERE group_num = ? order by user_id", GROUP['group_num'])
    START = GROUP['start']

    data = datatable(db, USERS, START, typ)
    data = addgoal(data, goal)
    data = projectwin(data, START)

    return render_template("index.html", groups=GROUPS, data=data, typ=typ, selectedGroup=GROUP)


# @app.route("/log_workout", methods=["GET", "POST"])
# @login_required
# def log_workout():
#     if request.method == "POST":
#         user = session["user_id"]
#         action = request.form.get("logwork")
#         print(f"action= ", action)
#         # TODO
#         # UPDATE if value already logged for selected day

#         # INSERT workout info
#         db.execute("INSERT INTO data VALUES (?, ?, ?, ?)", user, request.form.get("type"), request.form.get("log"), request.form.get("date"))
#         return render_template("log_workout.html")
#     else:
#         return render_template("log_workout.html")


@app.route("/signup", methods=["GET", "POST"])
@login_required
def signup():
    if request.method == "POST":
        #debug
        action = request.form["su_button"]
        user = session["user_id"]

        if action == "update":
            # SIGN UP TO EXISTING GROUP
            rows = db.execute("SELECT * FROM registry WHERE (user_id, group_num) = (?, ?)", user, request.form.get("signup"))
            if len(rows) != 0:
                # Error check - is user already signed up to selected group?
                return redirect("/")
            else:
                # Sign user up
                db.execute("INSERT INTO registry VALUES (?, ?)", user, request.form.get("signup"))
                return redirect("/")
        else:
            # CREATE NEW GROUP
            rows = db.execute("SELECT * FROM groups WHERE group_name == ?", request.form.get("groupname"))
            GROUPS = db.execute("SELECT group_name, group_num FROM groups")
            if len(rows) != 0:
                # Error check - is group name taken?
                return render_template("signup.html", groups=GROUPS, error=1)
            elif not request.form["groupname"] or not request.form["goal"]:
                # Error check - are group name and goal provided?
                return render_template("signup.html", groups=GROUPS, error=2)
            else:
                # add new group to groups table
                db.execute("INSERT INTO groups (group_name, type, goal, start) VALUES (?, ?, ?, ?)", request.form.get("groupname"), request.form.get("type"), request.form.get("goal"), date.today())
                # sign up user into new group
                group_num = db.execute("SELECT group_num FROM groups WHERE group_name = ?", request.form.get("groupname"))
                group_num = group_num[0]['group_num']
                db.execute("INSERT INTO registry VALUES (?, ?)", user, group_num)
                return redirect("/")
    else:
        GROUPS = db.execute("SELECT group_name, group_num FROM groups")
        return render_template("signup.html", groups=GROUPS)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE name = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", error=1)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Check if username exists
        exists = db.execute("SELECT * FROM users WHERE name = (?)", request.form.get("username"))
        if len(exists) >= 1:
             return render_template("register.html", error=1)

        # Ensure password and confirmation match
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("password and confirmation do not match", 400)

        # Register user if conditions are met
        else:
            username = request.form.get("username")
            passhash = generate_password_hash(request.form.get("password"))
            db.execute("INSERT INTO users (name, hash) VALUES (?, ?)", username, passhash);
            return redirect("/login")
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)