# Importing Flask modules
from flask import Flask, render_template, redirect, request
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from flask import session

# Set-up for database
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "c2VuZGhlbHA" # For when I add login/signup
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

# Webpage shortcuts
@app.route('/')
def render_homepage():
  return render_template('index.html')

@app.route('/dictionary/<cat_id>')
def render_dict_page(cat_id):
  return render_template('dictionary.html', 
                         categories = get_categories())

@app.route('/admin')
def render_admin():
  return render_template('admin.html')
  
@app.route('/login')
def render_login():
  return render_template('login.html')

@app.route('/signup')
def render_signup():
  return render_template('signup.html')

@app.route('/word_info/<word_id>')
def render_word_info(word_id):
  # Retrieving the information about the word requested
  word_info = get_list("SELECT * FROM words WHERE word_id = ?",word_id)
  
  return render_template('index.html', word_info)


app.run(host='0.0.0.0', port=81)
