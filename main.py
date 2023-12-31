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
  """Create connection to database."""
  try:
    connection = sqlite3.connect(db_file)
    return connection
  except Error as e:
    print(e)
  return None


# Functions to edit/retrieve data from to the database
def get_list(query, parameters):
  """Retrieve a list of data from the database w/wout parameters."""
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
  """Update the database with data and parameters."""
  con = create_connection(DATABASE)
  cur = con.cursor()
  cur.execute(query, parameters)
  con.commit()
  con.close()


def get_categories():
  """Retrieve all category ids, names."""
  cat_list = get_list("""SELECT * FROM categories 
  ORDER BY category_name""", "")
  return cat_list


def get_word_list():
  """Retrieve info of all words."""
  word_list = get_list("SELECT * FROM words ORDER BY word_name", "")
  return word_list

def append_alttext(words):
  """Create suitable alt texts for database images."""
  for i in words:
    word = list(i)
    if word[4]:
      image_name = word[4].split(".")
      alt_text = "A picture of " + image_name[0]
    else:
      alt_text = "No image displayed"

    word.append(alt_text)
  return(words)

# Login checking functions
def is_logged_in():
  """Check to see if the user is logged in or not."""
  print(session)
  if session.get("email") is None:
    print("Not logged in")
    return False
  else:
    print("Logged in")
    return True


def check_admin():
  """Check to see if the user is a teacher or student user."""
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
  return render_template('index.html',
                         logged_in=is_logged_in(),
                         teacher=check_admin(),
                         message=message)


@app.route('/admin')
def render_admin():
  message = request.args.get('message')
  if message is None:
    message = ""
  return render_template('admin.html',
                         words=get_word_list(),
                         categories=get_categories(),
                         logged_in=is_logged_in(),
                         teacher=check_admin(),
                         message=message)


@app.route('/login', methods=['POST', 'GET'])
def render_login():
  if is_logged_in():
    return redirect('/dictionary/category/1')
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

    except IndexError:
      return redirect("/login?message=Email+invalid+or+password+incorrect")

    # Validation for the password being correct
    if not bcrypt.check_password_hash(db_password, password):
      return redirect(request.referrer +
                      "?message=Email+invalid+or+password+incorrect")

    # Setting the session data
    session['email'] = email
    session['firstname'] = first_name
    session['user_id'] = user_id
    session['teacher'] = teacher
    return redirect('/')

  message = request.args.get('message')
  if message is None:
    message = ""
  return render_template('login.html',
                         logged_in=is_logged_in(),
                         teacher=check_admin(),
                         message=message)


@app.route('/logout')
def logout():
  for key in list(session.keys()):
    session.pop(key)
  return redirect('/?message=See+you+next+time!')


@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
  if is_logged_in():
    return redirect('/dictionary/category/1')

  # Retrieving data from form and validating
  if request.method == 'POST':
    fname = request.form.get('fname').title().strip()
    if len(fname) > 35:
      return redirect("/signup?error=First+name+maximum+length+is+35+characters")
       
    lname = request.form.get('lname').title().strip()
    if len(lname) > 35:
      return redirect("/signup?error=Last+name+maximum+length+is+35+characters")
      
    email = request.form.get('email').lower().strip()
    if len(email) > 320:
      return redirect("/signup?error=Email+maximum+length+is+320+characters")
      
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

    return redirect("/login?message=Signed+up")
  message = request.args.get('error')
  if message is None:
    message = ""
  return render_template('signup.html',
                         logged_in=is_logged_in(),
                         teacher=check_admin(),
                         message=message)


@app.route('/word_info/<int:word_id>', methods=['GET', 'POST'])
def render_word_info(word_id):
  words = get_list("SELECT * FROM words WHERE word_id = ?", [word_id])
  word_info = list(words[0])

  # Rtrieving the category and user who created the word from ids
  if not word_info[8]:
    word_info[8] = "1"
  users = get_list("SELECT first_name, last_name FROM users WHERE user_id = ?",
                   [word_info[8]])
  user = str(" ".join(users[0]).title())
  word_info[8] = user
  category = get_list(
    "SELECT category_name FROM categories WHERE category_id = ?",
    [word_info[7]])
  word_info[7] = " ".join(category[0]).title()

  # Setting alt-text
  if word_info[4]:
    image_name = word_info[4].split(".")
    alt_text = "A picture of " + image_name[0]
  else:
    alt_text = "No image displayed"
  word_info.append(alt_text)

  message = request.args.get('error')
  if message is None:
    message = ""

  return render_template('word_info.html',
                         word=word_info,
                         logged_in=is_logged_in(),
                         teacher=check_admin(),
                         message=message,
                         categories=get_categories())


# Menu Page Functions
@app.route('/dictionary/category/<cat_id>')
def render_dict_cat(cat_id):
  """Sorts the menu based on a given category."""
  current_category = get_list(
    """SELECT category_name 
  FROM categories 
  WHERE category_id = ?""", [cat_id])
  current_page = [str(current_category[0][0]).title(), "Levels"]
  words = get_list(
    """SELECT * FROM words WHERE category_id = ?
  ORDER BY word_name""", [cat_id])

  all_words = append_alttext(words)

  message = request.args.get('message')
  if message is None:
    message = ""

  return render_template('dictionary.html',
                         categories=get_categories(),
                         words=all_words,
                         logged_in=is_logged_in(),
                         teacher=check_admin(),
                         current_page=current_page,
                         message=message)


@app.route('/dictionary/level/<level>')
def render_dict_lev(level):
  """Sorts the menu based on a given level."""
  words = get_list(
    """SELECT * FROM words WHERE level = ?
  ORDER BY word_name""", [level])
  level_name = "Level " + level
  current_page = ["Categories", level_name]

  all_words = append_alttext(words)

  message = request.args.get('message')
  if message is None:
    message = ""

  return render_template('dictionary.html',
                         categories=get_categories(),
                         words=all_words,
                         logged_in=is_logged_in(),
                         teacher=check_admin(),
                         current_page=current_page,
                         message=message)


@app.route('/dictionary/search', methods=['GET', 'POST'])
def render_dict_search():
  """Sorts the menu based on a given string."""
  if request.method == 'POST':
    search_term = request.form['search'].strip().lower()
    words = get_list(
      """SELECT * FROM words
    WHERE word_name LIKE ? ORDER BY word_name""", ['%' + search_term + '%'])
    current_page = ["Categories", "Levels"]

    all_words = append_alttext(words)

  message = request.args.get('message')
  if message is None:
    message = ""

  return render_template('dictionary.html',
                         categories=get_categories(),
                         words=all_words,
                         logged_in=is_logged_in(),
                         teacher=check_admin(),
                         current_page=current_page,
                         message=message)


# Admin Functions
@app.route('/add_category', methods=['POST'])
def add_category():
  """Add a new category to the database."""
  if not is_logged_in() or not check_admin():
    return redirect('/?message=Need+to+be+logged+in.')
  if request.method == "POST":
    cat_name = request.form.get('cat_name').lower().strip()

    # Validate that the category name isn't too long for the database
    if len(cat_name) > 20:
      return redirect("/admin?message=Category+name+maximum+length+is+20+characters")
    
    con = create_connection(DATABASE)
    query = "INSERT INTO categories ('category_name') VALUES (?)"
    cur = con.cursor()
    cur.execute(query, (cat_name, ))
    con.commit()
    con.close()
    return redirect('/admin?message=Category+added')


@app.route('/delete_category', methods=['POST'])
def render_delete_category():
  """Remove a category to the database."""
  if not is_logged_in() or not check_admin():
    return redirect('/?message=Need+to+be+logged+in.')
  if request.method == "POST":
    category = request.form.get('cat_id')
    category = category.split(", ")
    cat_id = category[0]
    cat_name = category[1].title()

    message = request.args.get('error')
    if message is None:
      message = ""

    return render_template('confirm_delete.html',
                           id=cat_id,
                           name=cat_name,
                           type="category",
                           message=message)
    return redirect("/admin")


@app.route('/delete_category_confirm/<int:cat_id>')
def delete_category_confirm(cat_id):
  """Confirm the deletion of a category from the database."""
  if not is_logged_in() or not check_admin():
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
  """Add a word to the dictionary."""
  if not is_logged_in() or not check_admin():
    return redirect('/?message=Need+to+be+logged+in.')
  if request.method == "POST":
    # Retrieving values and validating
    name = request.form.get("name").lower().strip()
    if len(name) > 85:
      return redirect("/admin?message=Word+name+maximum+length+is+85+characters")
      
    english = request.form.get("english").strip()
    if len(english) > 85:
      return redirect("/admin?message=English+maximum+length+is+85+characters")
      
    description = request.form.get("description")
    if description:
      description.strip()
    else:
      description = "Pending"
    if len(description) > 300:
      return redirect("/admin?message=Description+maximum+length+is+300+characters")

    
    level = request.form.get("level").strip()
    image = request.form.get("image")
    if image:
      image.strip()
      if len(image) > 256:
        return redirect("/admin?message=Image+maximum+length+is+256+characters")
    else:
      image = None
      
    category = request.form.get("cat_id").strip() 
    user = str(session.get('user_id'))
    time = str(datetime.datetime.now())

    con = create_connection(DATABASE)
    query = """INSERT INTO words ('word_name', 'english','description', 'image', 'level', 'category_id', 'user_id', 'entry_date') 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
    cur = con.cursor()
    cur.execute(
      query, (name, english, description, image, level, category, user, time))
    con.commit()
    con.close()
    return redirect("/admin?message=Word+added")


@app.route('/delete_word', methods=['POST'])
def delete_word():
  """Delete a word from the dictionary."""
  if not is_logged_in() or not check_admin():
    return redirect('/?message=Need+to+be+logged+in.')
  if request.method == "POST":
    items = request.form.get('word_id')
    if items is None:
      return redirect("/admin?message=No+item+selected")

    word = items.split(", ")
    word_id = word[0]
    word_name = word[1].title() if len(word) > 1 else ""

    message = request.args.get('message')
    if message is None:
      message = ""

    return render_template('confirm_delete.html',
                           id=word_id,
                           name=word_name,
                           type="word",
                           message=message)
    return redirect("/admin")


@app.route('/delete_word_confirm/<int:word_id>')
def delete_item_confirm(word_id):
  """Confirm the deletion of a word from the database."""
  if not is_logged_in() or not check_admin():
    return redirect('/?message=Need+to+be+logged+in.')
  con = create_connection(DATABASE)
  query = "DELETE FROM words WHERE word_id = ?"
  cur = con.cursor()
  cur.execute(query, (word_id, ))
  con.commit()
  con.close()

  return redirect("/admin")


@app.route('/edit/<int:word_id>/<type>', methods=['POST'])
def edit_word(word_id, type):
  """Edit a value of a word from the dictionary."""
  if not is_logged_in() or not check_admin():
    return redirect('/?message=Need+to+be+logged+in.')

  # Retrieve the new value
  if request.method == "POST":
    value = request.form.get('value')
    if value is None:
      return redirect("/?error=No+value+selected")

    # Validating
    if type == "word_name":
      if len(value) > 85:
        return redirect("/?message=Word+name+maximum+length+is+85+characters")
    elif type == "english":
      if len(value) > 85:
        return redirect("/?message=English+maximum+length+is+85+characters")
    elif type == "description":
      if len(value) > 300:
        return redirect("/?message=Description+maximum+length+is+300+characters")
    elif type == "image":
      if len(value) > 256:
        return redirect("/?message=Image+maximum+length+is+256+characters")

    # Updating the database
    query = str("UPDATE words SET " + type + " = ? WHERE word_id = ?")
    put_data(query, (value, word_id))

    return redirect("/?message=Updated+information")


app.run(host='0.0.0.0', port=81)
