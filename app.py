
import ast
import os
import fitz
import secrets
from cs50 import SQL
from datetime import date
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from email_validator import validate_email, EmailNotValidError
from flask import Flask, flash, redirect, render_template, request, session, url_for
from helpers import ForgottenForms, bienvenido, check_password_strength, clean_user_input, graci, gracias, list_to_string, login_required, apology, titlecase, BookForm
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv


load_dotenv()


# Configure application
app = Flask(__name__)
secret_key = secrets.token_hex(16)
# app.secret_key = "_53oi3uriq9pidklsfner7t8weipoqlpl"
csrf = CSRFProtect(app)

app.config["SECRET_KEY"] = secret_key
app.config["UPLOAD_FOLDER"] = "static/files/books"
app.config["UPLOAD_IMG_FOLDER"] = "static/files/book_covers"

# Flask-Mail configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
mail = Mail(app)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///library.db")

# Serializer for token generation
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    """Display Welcome page"""
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user into library after Validating input"""

    if request.method == "POST":
        # Ensure Full name was submitted
        if not request.form.get("fullname").strip():
            return apology("must provide Name", 400)
        
       # Ensure username was submitted
        elif not request.form.get("username").strip():
            return apology("must provide username", 400)

        # Query database for if username already exist
        elif db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username")):
            return apology("username already exits", 400)

        # Ensure password was submitted
        elif not request.form.get("password").strip():
            return apology("must provide password", 400)

        # Ensure both passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password do not match confirmation password", 400)

        # Validate E-mail provided
        email = request.form.get("mail")
        try:
            email = validate_email(email).email
        except EmailNotValidError as err:
            return apology(f"{err}", 400)
        
        password = check_password_strength(request.form.get("password").strip())
        if not password:

            # add registrant to database
            name = titlecase(str(request.form.get("fullname"))).strip()
            db.execute("INSERT INTO users (name, username, mail, hash) VALUES(?, ?, ?, ?)",
                name, str(request.form.get("username").strip()),
                email, generate_password_hash(password))

            # Send Welcome mail to new user
            mail.send(graci(email, name))
        else:
            return apology(f"Password requires at least {password}", 400)

        # redirect user to login
        return redirect("/login")
        # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # form = LoginForm
    # User reached route via POST as by submitting a form via POST
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("please provide username", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("please provide password", 400)

        # Query database for username
        try:
            validate_email(str(request.form.get("username")))
            rows = db.execute(
                "SELECT * FROM users WHERE mail LIKE ?", str(request.form.get("username").strip())
            )

            # Ensure username exists and password is correct
            if len(rows) != 1 or not check_password_hash(
                rows[0]["hash"], request.form.get("password")
            ):
                return apology("Invalid mail and/or password", 400)
        except EmailNotValidError:
        # elif not validate_email(str(request.form.get("username").strip())):
            rows = db.execute(
                "SELECT * FROM users WHERE username LIKE ?", str(request.form.get("username").strip())
            )

            # Ensure username exists and password is correct
            if len(rows) != 1 or not check_password_hash(
                rows[0]["hash"], request.form.get("password")
            ):
                return apology("Invalid username and/or password", 400)
            
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["name"] = rows[0]["name"]
        session["username"] = rows[0]["username"]

        # Get all admins in database create an admin session list of admin user
        admins = db.execute("SELECT user_id FROM admins")
        session["admins"] = [admin["user_id"] for admin in admins] # session["admins"] is a list
        user_id = rows[0]["id"]
        if user_id == 1 and user_id not in session.get("admins", []):
            db.execute("INSERT INTO admins (user_id) VALUES (?)", user_id)


        # Redirect user to home page
        return redirect("/")

        # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
    

@app.route("/addbook", methods=["GET", "POST"])
@login_required
def addbook():
    """Administrators control"""

    form = BookForm()

    if request.method == "POST" and form.validate_on_submit():
        title = form.title.data.strip()
        publisher = form.publisher.data.strip()
        year = form.year.data.strip()
        isbn = form.isbn.data.strip()
        _author = form.author.data
        _country = form.country.data
        _birth = form.birth.data

        # Check if book already exist
        check_books = db.execute("SELECT isbn FROM books")
        if isbn in [row["isbn"] for row in check_books]:
            return "Book Already In Database"
        
        pdf_file = form.pdf_file.data
        if "pdf_file" in form.errors:
            flash(form.errors["pdf_file"][0], "danger")
        pdf_filename = os.path.join(app.config["UPLOAD_FOLDER"], pdf_file.filename)
        pdf_file.save(pdf_filename)

        cover_image = form.cover_image.data
        if "cover_image" in form.errors:
            flash(form.errors["cover_image"][0], "danger")
        cover_filename = os.path.join(app.config["UPLOAD_IMG_FOLDER"], cover_image.filename)
        cover_image.save(cover_filename)

        # Get number of pages
        try:
            pdf_document = fitz.open(pdf_filename)
            num_pages = pdf_document.page_count
        except Exception as err:
            # If form validation fails or it's a GET request, flash an error message
            flash(f"Error: {err}.")
            pdf_document.close()
            return redirect(request.url)
        finally:
            if pdf_document:
                pdf_document.close()

        
        # Make insertions into tables

        db.execute("BEGIN TRANSACTION")
        names = db.execute("SELECT publisher FROM publishers")
        if titlecase(publisher) in [row["publisher"] for row in names]:
            pub_id = db.execute("SELECT id FROM publishers WHERE publisher = ?", titlecase(publisher))[0]["id"]
        else:
            pub_id = db.execute("INSERT INTO publishers (publisher) VALUES (?)", titlecase(publisher))

        book_id = db.execute("INSERT INTO books (isbn, title, year, publisher_id, pages) VALUES (?, ?, ?, ?, ?)", isbn, titlecase(title), year, pub_id, num_pages)
        db.execute("INSERT INTO files (book_id, book_path, book_img_path) VALUES (?, ?, ?)", book_id, pdf_filename, cover_filename)
        
        # INSERT author(s) info into authors table and book/author ids into authored table
        if "," in _author:
            author = list_to_string(_author)
            country = list_to_string(_country)
            birth = list_to_string(_birth)
            for i in range(len(author)):
                author_id = get_author_id(author[i], clean_user_input(country[i]), birth[i])
                db.execute("INSERT INTO authored (author_id, book_id) VALUES (?, ?)", author_id, book_id)
        else:
            author_id = get_author_id(_author, clean_user_input(_country), _birth)
            db.execute("INSERT INTO authored (author_id, book_id) VALUES (?, ?)", author_id, book_id)

        
        # Redirect Admin to Book Shelf to see the new book uploaded
        db.execute("COMMIT")
        return redirect(url_for('shelf'))

    return render_template("addbook.html", form=form)


@app.route("/recommendation", methods=["GET", "POST"])
@login_required
def recommend():
    title = ""
    if request.method == "POST":
        suggestion = request.form.get("newBook").strip()
        db.execute("INSERT INTO recommendations (user_id, recommendation) VALUES (?, ?)", session["user_id"], suggestion)
        return redirect(url_for("shelf"))
    return render_template("recommend.html", title=title)


@app.route("/logout")
def logout():
    """Log user out by forgetting any user_id and redirect user to login"""
    session.clear()
    return redirect("/")


@app.route("/new_admin", methods=["GET", "POST"])
def admins():
    users = db.execute("SELECT * FROM users")
    admins = db.execute("SELECT user_id FROM admins")
    admin_ids = [admin["user_id"] for admin in admins]
    session["admins"] = admin_ids


    if request.method == "POST":
        id = request.form.get("id")
        name = request.form.get("name")
        email = request.form.get("mail")
        db.execute("INSERT INTO admins (user_id) VALUES (?)", id)

        # Send an email to the newly added admin
        mail.send(gracias(email, name))

        # mail = request.form.get("mail")
        return f"{name} is now an Admin"
    
    return render_template("newadmin.html", users=users, admins=admin_ids)

@app.route("/de_admin", methods=["POST"])
def unadmin():
    id = request.form.get("id")
    email = request.form.get("mail")
    name = request.form.get("name")
    db.execute("DELETE FROM admins WHERE user_id = ?", id)
    
    # Send a Welcome mail to the new admin
    mail.send(bienvenido(email, name))

    return f"{name} is no longer an Admin"

@app.route("/suggestionsPage", methods=["GET", "POST"])
def suggest():
    suggestions = db.execute("SELECT * FROM suggestions")
    if request.method == "POST":
        text = request.form.get("suggest")
        db.execute("DELETE FROM recommendations WHERE recommendation = ?", text)
        return redirect(request.url)
    return render_template("suggestion.html", suggestions=suggestions)


@app.route("/shelf", methods=["GET", "POST"])
@login_required
def shelf():
    """Display books and their information"""
    data = db.execute("SELECT * FROM longlist ORDER BY book_title")
    today = date.today()
    # Query all information needed for downloading the book
    if request.method == "POST":
        text = titlecase(request.form.get("search").strip())
        if row := db.execute("SELECT * FROM longlist WHERE book_title LIKE ?", f'%{text}%'):
            return render_template("shelf.html", data=row, today=today)
        elif row1 := db.execute("SELECT * FROM longlist WHERE author_name LIKE ?", f'%{text}%'):
            return render_template("shelf.html", data=row1, today=today)
        else:
            return render_template("recommend.html", title=text)
    return render_template("shelf.html", data=data, today=today)

@app.route("/del_book", methods=["POST"])
def del_book():
    book_id = request.form.get("book_id")
    if book_id:
        row = db.execute("SELECT * FROM files WHERE book_id = ?", book_id)
        book_pdf = row[0]["book_path"]
        cover_img = row[0]["book_img_path"]
        db.execute("DELETE FROM books WHERE id = ?", book_id)
        os.remove(cover_img)
        os.remove(book_pdf)
    return redirect("/shelf")

# Endpoint to request a password reset
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    form = ForgottenForms()
    if request.method == "POST" and form.validate_on_submit():

        email = form.email.data
        user = get_user_by_email(email)

        if user:
            token = generate_reset_token(email)
            send_reset_email(email, token)
            flash("Check your email for a password reset link.", "success")
        else:
            flash("Email not found. Please check your input.", "error")

    return render_template("forgot_password.html", form=form)

# Endpoint to reset password (via link in email)
@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, max_age=3600)  # Token expires after 1 hour
    except:
        flash("Invalid or expired reset link. Please request a new one.", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("new_password").strip()
        update_password(email, new_password)
        flash("Password reset successfully. You can now log in with your new password.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)

# Helper function to get a user by email from the database
def get_user_by_email(email):
    user = db.execute("SELECT * FROM users WHERE mail = ?", email)
    return user[0] if user else None

# Helper function to generate a reset token
def generate_reset_token(email):
    return serializer.dumps(email)

# Helper function to send a reset email 
def send_reset_email(email, token):
    reset_url = url_for("reset_password", token=token, _external=True)
    subject = "Password Reset Request"
    body = f"To Reset Your Password \n Click the following link to reset your password: {reset_url} \n This link will expire in 1hour"
    msg = Message(subject, recipients=[email], body=body)
    mail.send(msg)

# Helper function to update the password in the database
def update_password(email, new_password):
    db.execute("UPDATE users SET hash = ? WHERE mail = ?", generate_password_hash(new_password), email)

# Helper function for getting Author id
def get_author_id(author_name, country, birth):
    # Check if the author already exists in the authors table
    result = db.execute("SELECT id FROM authors WHERE name = ? AND country = ? AND birth = ?", titlecase(author_name), country, birth)

    # If there is a result, return the existing author_id
    if result:
        return result[0]["id"]
    else:
        # If the author doesn't exist, insert the new author
        last_id = db.execute("INSERT INTO authors (name, country, birth) VALUES (?, ?, ?)", titlecase(author_name), country, birth)
        
        # Get the last inserted ID using lastrowid
        return last_id
    
if __name__ == "__main__":
    app.run(debug=True)