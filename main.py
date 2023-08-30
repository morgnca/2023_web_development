# Importing Flask modules
from flask import Flask, render_template, redirect, request
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from flask import session
import datetime

# Set-up for database, constants
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "c2VuZGhlbHA"
DATABASE = "dictionary.db"
STUDENT_EMAIL = "student"

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

def get_word_list():
  """Retrieve info of all words"""
  word_list = get_list("SELECT * FROM words","")
  return word_list

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
  message = request.args.get('message')
  if message is None:
    message = ""
  return render_template('index.html',logged_in=is_logged_in(),
                         teacher=check_admin(), message=message)

@app.route('/dictionary/<cat_id>')
def render_dict_page(cat_id):
  current_category = get_list("""SELECT category_name 
  FROM categories 
  WHERE category_id = ?""", [cat_id])
  current_page = str(current_category[0][0]).title()
  words = get_list("SELECT * FROM words WHERE category_id = ?",
                   [cat_id])
  for i in words:
    print(i)
  
  return render_template('dictionary.html', 
                         categories = get_categories(), words=words,
                        logged_in=is_logged_in(), teacher=check_admin(),
                        current_page=current_page)

@app.route('/admin')
def render_admin():
  return render_template('admin.html', words = get_word_list(), 
                         categories =get_categories(),
                         logged_in=is_logged_in(),
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
      return redirect("/login?error=Email+invalid+or+password+incorrect")

    # Validation for the password being correct
    if not bcrypt.check_password_hash(db_password, password):
      return redirect(request.referrer + "?message=Email+invalid+or+password+incorrect")

    # Setting the session data
    session['email'] = email
    session['firstname'] = first_name
    session['user_id'] = user_id
    session['teacher'] = teacher
    print(session)
    return redirect('/')
    
  
  message = request.args.get('message')
  print(message)
  if message is None:
    message = ""
  return render_template('login.html', logged_in=is_logged_in(),
                         teacher=check_admin(), message=message)

@app.route('/logout')
def logout():
  print(list(session.keys()))
  for key in list(session.keys()):
    session.pop(key)
  print(list(session.keys()))
  return redirect('/?message=See+you+next+time!')

@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
  if is_logged_in():
      return redirect('/dictionary/1')
  if request.method == 'POST':
    print(request.form)
    fname = request.form.get('fname').title().strip()
    lname = request.form.get('lname').title().strip()
    email = request.form.get('email').lower().strip()
    password = request.form.get('password')
    password2 = request.form.get('password2')
    teacher = 1

    if password != password2:
      return redirect("/signup?error=Passwords+do+not+match")

    if len(password) < 8:
      return redirect("/signup?error=Password+must+be+at+least+8+characters")

    hashed_password = bcrypt.generate_password_hash(password)

    # Assign the user a student or teacher account
    if not request.form.get('teacher') or STUDENT_EMAIL in email:
      teacher = 0
      

    con = create_connection(DATABASE)
    query = """INSERT INTO users 
    (first_name, last_name, email, password, teacher) 
    VALUES (?, ?, ?, ?, ?)"""
    cur = con.cursor()

    try:
      cur.execute(query, (fname, lname, email, hashed_password, teacher))
    except sqlite3.IntegrityError:
      con.close()
      return redirect('/signup?error=Email+is+already+used')

    con.commit()
    con.close()

    return redirect("/login")
  message = request.args.get('error')
  print(message)
  if message is None:
    message = ""
  return render_template('signup.html',logged_in=is_logged_in(),
                         teacher=check_admin(), message=message)

@app.route('/word_info/<word_id>')
def render_word_info(word_id):
  word_info = get_list("SELECT * FROM words WHERE word_id = ?",[word_id])
  
  return render_template('index.html', word_info,logged_in=is_logged_in(),
                         teacher=check_admin())

# Admin Functions
@app.route('/add_category', methods=['POST'])
def add_category():
  """Add a new category to the database"""
  if not is_logged_in():
    return redirect('/?error=Need+to+be+logged+in.')
  if request.method == "POST":
    print(request.form)
    cat_name = request.form.get('name').lower().strip()
    print(cat_name)
    con = create_connection(DATABASE)
    query = "INSERT INTO categories ('category_name') VALUES (?)"
    cur = con.cursor()
    cur.execute(query, (cat_name, ))
    con.commit()
    con.close()
    return redirect('/admin')

@app.route('/delete_category', methods=['POST'])
def render_delete_category():
  """Remove a new category to the database"""
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')
  if request.method == "POST":
    category = request.form.get('cat_id')
    print(category)
    category = category.split(", ")
    cat_id = category[0]
    cat_name = category[1]
    return render_template('confirm_delete.html', id=cat_id, name=cat_name, type="category")
    return redirect("/admin")

@app.route('/delete_category_confirm/<int:cat_id>')
def delete_category_confirm(cat_id):
  """Confirm the deletion of a category from the database"""
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')
  con = create_connection(DATABASE)
  query = "DELETE FROM categories WHERE category_id = ?"
  cur = con.cursor()
  cur.execute(query, (cat_id, ))
  con.commit()
  con.close()
  return redirect("/admin")

@app.route('/add_word', methods=['POST'])
def add_word():
  """Add a word to the dictionary using data from a form"""
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')
  if request.method == "POST":
    print(request.form)
    name = request.form.get("name").lower().strip()
    english = request.form.get("english").strip()
    description = request.form.get("description")
    if description:
      description.strip()
    else:
      description = "Pending"
    level = request.form.get("level").strip()
    image = request.form.get("image")
    if image:
      image.strip()
    else:
      image = None
    category = request.form.get("cat_id").strip()
    user = str(session.get('user_id'))
    time = str(datetime.datetime.now())
    print(name, english, description, level, image, category, user, time)

    con = create_connection(DATABASE)
    query = """INSERT INTO words ('word_name', 'english','description', 'image', 'level', 'category_id', 'user_id', 'entry_date') 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
    cur = con.cursor()
    cur.execute(query, (name, english, description, image, level, category, user, time))
    con.commit()
    con.close()
    return redirect("/admin")

@app.route('/delete_word', methods=['POST'])
def delete_word():
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')
  if request.method == "POST":
    items = request.form.get('word_id')
    if items is None:
      return redirect("/admin?error=No+item+selected")
    print(items)

    word = items.split(", ")
    word_id = word[0]
    word_name = word[1] if len(word) > 1 else ""
    return render_template('confirm_delete.html', id=word_id, name=word_name, type="word")
    return redirect("/admin")

@app.route('/delete_word_confirm/<int:word_id>')
def delete_item_confirm(word_id):
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')
  con = create_connection(DATABASE)
  query = "DELETE FROM words WHERE word_id = ?"
  cur = con.cursor()
  cur.execute(query, (word_id, ))
  con.commit()
  con.close()
  return redirect("/admin")


app.run(host='0.0.0.0', port=81)