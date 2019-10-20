from flask import Flask, render_template, request, flash, session, redirect
import re
import md5
from mysqlconnection import MySQLConnector

app = Flask(__name__)

app.secret_key = "dirtylittlesecret"
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
mysql = MySQLConnector(app, "wall")

@app.route('/')
def index():
    return render_template('index.html')

#route to accept the submitted form and validate it
@app.route('/register', methods=["POST"])
def register():
    is_valid = True
    #email validations
    if len(request.form["email"]) == 0:
        flash("Email field is required")
        is_valid = False
    elif not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid email")
        is_valid = False

    #first name validations
    if len(request.form["fname"]) < 0:
        flash("First name is required")
        is_valid = False
    elif not request.form["fname"].isalpha():
        flash("Invalid first name")
        is_valid = False

    #last name validations
    if len(request.form["lname"]) < 0:
        flash("Last name is required")
        is_valid = False
    elif not request.form["lname"].isalpha():
        flash("Invalid last name")
        is_valid = False

    #password validations
    if len(request.form["pw"]) < 8:
        flash("Password must be at least 8 characters")
        is_valid = False
    elif request.form["pw"] != request.form["confpw"]:
        flash("Passwords do not match")
        is_valid = False

    if is_valid:
        pw = md5.new(request.form["pw"]).hexdigest()
        add_user = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:fn, :ln, :em, :pw, NOW(), NOW())"
        user_data = { 'fn': request.form["fname"],
                      'ln': request.form["lname"],
                      'em': request.form["email"],
                      'pw': pw}
        user_id = mysql.query_db(add_user, user_data)
        #set user in session
        session["name"] = request.form["fname"]
        session["user_id"] = user_id
        return redirect('/wall')

    return redirect('/')

@app.route('/login', methods=["POST"])
def login():
    #is there a user with that email in my db?
    pw = md5.new(request.form['pw']).hexdigest()
    find_user_q = "SELECT * FROM users WHERE email = :email and password = :pw"
    data = { 'email': request.form["email"], 'pw': pw}
    found_user = mysql.query_db(find_user_q, data)

    #no user with that email
    if len(found_user) == 0:
        flash("No user registered with that email")
    else:
        #if so, does the password they entered match what is in the db?
        if found_user[0]["password"] != pw:
            flash("Password is incorrect")
        else:
            #set user in session
            session["name"] = found_user[0]["first_name"]
            session["user_id"] = found_user[0]["user_id"]
            print 'about to redirect to wall route'
            return redirect('/wall')
    return redirect('/')

@app.route('/wall')
def show_wall():
    if 'name' not in session:
        print 'name not in session'
        return redirect('/')
    else:
        show_messages_q = "SELECT users.first_name, users.last_name, messages.message_text, messages.created_at, messages.updated_at, messages.message_id FROM messages JOIN users ON messages.user_id = users.user_id"
        marchive = mysql.query_db(show_messages_q)

        show_comments_q = "SELECT users.first_name, users.last_name, messages.message_text, messages.created_at, messages.updated_at, messages.message_id, comments.comment_text, comments.created_at, comments.updated_at, comments.comment_id FROM comments JOIN users ON comments.user_id = users.user_id JOIN messages ON comments.message_id = messages.message_id"
        carchive = mysql.query_db(show_comments_q)
        return render_template('wall.html', carchive=carchive, marchive=marchive)

@app.route('/message', methods=['POST'])
def create_message():
    print 'in messages'
    create_message_query = 'INSERT INTO messages (message_text, created_at, updated_at, user_id) VALUES (:mtext, now(), now(), :user_id)'
    message_data = {
        'mtext' : request.form['message'],
        'user_id': session['user_id']
    }
    mysql.query_db(create_message_query, message_data)
    print 'leaving messages'
    return redirect('/wall')

@app.route('/comment', methods=['POST'])
def create_comment():
    create_comment_query = 'INSERT INTO comments (comment_text, created_at, updated_at, user_id, message_id) VALUES (:ctext, now(), now(), :user_id, :message_id)'
    comment_data = {
        'ctext' : request.form['comment'],
        'user_id': session['user_id'],
        'message_id': request.form['message_id']
    }
    mysql.query_db(create_comment_query, comment_data)
    return redirect('/wall')

@app.route('/logout')
def logout():
    if 'name' not in session:
        print not 'clearing session'
        return redirect ('/')
    session.pop('name')
    return redirect('/')

app.run(debug=True)