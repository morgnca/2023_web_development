# Importing Flask modules
from flask import Flask, render_template, redirect, request
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from flask import session

# Set-up for database
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "c2VuZGhlbHA"
DATABASE = "dictionary.db"

def create_connection(db_file):
  """Create connection to database"""
  try:
    connection = sqlite3.connect(db_file)
    return connection
  except Error as e:
    print(e)
  return None

# Functions to edit/retrieve data from to the database
def get_list(query, parameters):
  """Retrieve a list of data from the database w/wout parameters"""
  con = create_connection(DATABASE)
  cur = con.cursor()
  if parameters == "":
    cur.execute(query)
  else:
    cur.execute(query, parameters)
  query_list = cur.fetchall()
  con.close()
  return query_list

def put_data(query, parameters):
  """Update the database with data and parameters"""
  con = create_connection(DATABASE)
  cur = con.cursor()
  cur.execute(query, parameters)
  con.commit()
  con.close()

def get_categories():
  """Retrieve all category ids, names"""
  cat_list = get_list("SELECT * FROM categories","")
  return cat_list

# Login checking functions
def is_logged_in():
  """Check to see if the user is logged in or not"""
  print(session)
  if session.get("email") is None:
    print("Not logged in")
    return False
  else:
    print("Logged in")
    return True 

def check_admin():
  """Check to see if the user is a teacher or student user"""
  if is_logged_in():
    if session.get("teacher") == 1:
      print("Teacher user")
      return True
    else:
      print("Student user")
      return False

# Webpage shortcuts
@app.route('/')
def render_homepage():
  return render_template('index.html',logged_in=is_logged_in(),
                         teacher=check_admin())

@app.route('/dictionary/<cat_id>')
def render_dict_page(cat_id):
  words = get_list("SELECT * FROM words WHERE category_id = ?",
                   [cat_id])
  return render_template('dictionary.html', 
                         categories = get_categories(), words=words,
                        logged_in=is_logged_in(), teacher=check_admin())

@app.route('/admin')
def render_admin():
  return render_template('admin.html',logged_in=is_logged_in(),
                         teacher=check_admin())
  
@app.route('/login', methods=['POST', 'GET'])
def render_login():
  if is_logged_in():
    return redirect('/dictionary/1')
  print("Logging in")
  if request.method == 'POST':
    email = request.form['email'].strip().lower()
    password = request.form['password'].strip()

    query = "SELECT user_id, first_name, teacher, password FROM users WHERE email = ?"
    user_data = get_list(query, [email])
    # Validates setting data for session
    try:
      user_id = user_data[0][0]
      first_name = user_data[0][1]
      teacher = user_data[0][2]
      db_password = user_data[0][3]
      print(user_id, first_name, teacher, db_password)
      
    except IndexError:
      return ("redirect/login?error=Email+invalid+or+password+incorrect")

    # Validation for the password being correct
    if not bcrypt.check_password_hash(db_password, password):
      return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

    # Setting the session data
    session['email'] = email
    session['firstname'] = first_name
    session['user_id'] = user_id
    session['teacher'] = teacher
    print(session)
    return redirect('/')
    
  return render_template('login.html', logged_in=is_logged_in(),
                         teacher=check_admin())

@app.route('/logout')
def logout():
  print(list(session.keys()))
  [session.pop(key) for key in list(session.keys())]
  print(list(session.keys()))
  return redirect('/?message=See+you+next+time!')

@app.route('/signup')
def render_signup():
  return render_template('signup.html',logged_in=is_logged_in(),
                         teacher=check_admin())

@app.route('/word_info/<word_id>')
def render_word_info(word_id):
  word_info = get_list("SELECT * FROM words WHERE word_id = ?",[word_id])
  
  return render_template('index.html', word_info,logged_in=is_logged_in(),
                         teacher=check_admin())


app.run(host='0.0.0.0', port=81)