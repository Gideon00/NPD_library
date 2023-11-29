# Helpers function for the library program


import ast
import re
import pycountry
from functools import wraps
from wtforms.validators import ValidationError
from email_validator import EmailNotValidError, validate_email
from flask_wtf import FlaskForm
from flask_mail import Message
from flask_wtf.file import FileField, FileAllowed
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length
from flask import redirect, render_template, session
from password_strength import PasswordPolicy


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("username") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Capitalize first letter in string
def titlecase(s):
    """
    Returns A String WIth Every Word Capitalized.
    
    """
    return re.sub(r"[A-Za-z]+('[A-Za-z]+)?", lambda mo: mo.group(0).capitalize(), s)

# Check Password
policy = PasswordPolicy.from_names(
    length=6,  # minimum length: 8 characters
    uppercase=1,  # need min. 1 uppercase letters
    numbers=1,  # need min. 1 digits
    special=1,  # need min. 1 special characters
)

def check_password_strength(password):
    return policy.test(password)

# Create class for form
class BookForm(FlaskForm):

    def __init__(self, *args, **kwargs):
        super(BookForm, self).__init__(*args, **kwargs)

        # Custom list with preferred order
        self.preferred_countries = [
        "US",  # United States
        "CA",  # Canada
        "GB",  # United Kingdom
        "NG",  # Nigeria
        "IN",  # India
        ]  # Add more as needed

        # Use pycountry to get a list of countries dynamically
        self.all_countries = list(pycountry.countries)

        # Sort the countries to put preferred ones on top
        self.all_countries.sort(key=lambda x: (
            self.preferred_countries.index(x.alpha_2) if x.alpha_2 in self.preferred_countries else float('inf'),
            x.name
        ))

        self.country_choices = [(country.name, country.name) for country in self.all_countries]

        # Assign choices to the SelectField
        self.country.choices = self.country_choices


    title = StringField("Title", validators=[DataRequired(message="Title is required.")])
    publisher = StringField("Publisher", validators=[DataRequired(message="Publisher name is required")])
    author = StringField("Author", validators=[DataRequired(message="Author(s) name is required")])
    country = StringField("Country", validators=[DataRequired(message="Country of Author required")])
    birth = StringField("Birth", validators=[DataRequired(message="Birthdate of Author required")])
    year = StringField("Year", validators=[DataRequired(message="Release Year of Book required")])
    isbn = StringField("ISBN", validators=[DataRequired(message="ISBN Number required")])
    pdf_file = FileField("PDF File", validators=[DataRequired(message="PDF file of Book required"), FileAllowed(["pdf", "epub", "txt", "ibooks", "lit", "azw", "azw3"], "Only images are allowed!")])
    cover_image = FileField("Book Cover Image", validators=[DataRequired(message="Cover Image of Book required"), FileAllowed(["jpg", "png", "jpeg", "bmp"], "Only images are allowed!")])

class ForgottenForms(FlaskForm):
    email = StringField("Email")
    submit = SubmitField("Submit")

    def validate_email(self, field):
        try:
            # Validate the email using the email-validator library
            validate_email(field.data)
        except EmailNotValidError as e:
            raise ValidationError(str(e))
        
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(message="Username is required.")])
    password = PasswordField("Password", validators=[DataRequired(),
                    Length(min=8, message='Password must be at least 8 characters long')])

def list_to_string(author):
    # Split the string using both methods and combine the results
    names_list = [name.strip() for part in author.split(",") for name in part.split(", ")]
    return names_list

def clean_user_input(user_input):
    # Convert user input to lowercase for case-insensitive comparison
    user_input_lower = user_input.lower()

    # Check if user input matches a country name
    for country in pycountry.countries:
        if user_input_lower == country.name.lower():
            return country.name

    # Check if user input matches a country code
    for country in pycountry.countries:
        if user_input_lower == country.alpha_2.lower() or user_input_lower == country.alpha_3.lower():
            return country.name

    # If no match is found, return None or handle as needed
    return None

# Helper function to send new users mail
def graci(email, name):
    subject = "Welcome to the National Prayer Department's Library"
    body = f"""
        Hello {name},

        🙏 Thank you for Signing up with Us! 🙏

        You are now registered as a member of The National Prayer Department's
        Library!

        feel free to search your favourite books, download them and also make recommendations,
        for other valuable books you feel we need to add to our database

        Stay Stuffy,

        © rabboni
        eLibrary Developer
        National Prayer Department
        """
    return Message(subject, recipients=[email], body=body)

# Helper functions to send Admin mail
def gracias(email, User):
    subject = "Appreciation for Your Service to the National Prayer Department"
    body = f"""
        Dear {User},

        🙏 Thank you for your dedicated service! 🙏

        We extend our gratitude for the time you spent as an Admin for NPD's eLibrary.
        While you may no longer hold the Admin role, your contributions were invaluable,
        and we want you to know that your efforts were truly appreciated.

        Although your role has changed, we encourage you to continue engaging with our library.
        Feel free to recommend more books and explore the vast collection at your leisure.
        Your insights and recommendations remain a valuable part of our community.

        Thank you, comrade, for your commitment and support.
        We look forward to your continued involvement with NPD's eLibrary.

        Best regards,

        © rabboni
        eLibrary Developer
        National Prayer Department
        """
    return Message(subject, recipients=[email], body=body)

def bienvenido(email, User):
    subject = "Your New Role as Admin in NPD's eLibrary"
    body = f"""
        Dear {User},

        🎉 Congratulations! 🎉

        We are delighted to inform you that you have been appointed as the newest Admin of NPD's eLibrary.
        Welcome aboard! Your dedication and expertise have earned you this significant responsibility.

        As an Admin, you will play a crucial role in enhancing our eLibrary experience.
        Your responsibilities include:

        Adding new books to the library.
        Reviewing and incorporating recommended books from other users.
        Granting admin privileges to other individuals.
        Managing the removal of books from the library when necessary.
        We are eager to leverage your skills to elevate the eLibrary,
        and we encourage you to log in promptly so we can begin this exciting journey together.

        Thank you for your commitment to NPD's eLibrary.
        We look forward to achieving great milestones with you as part of our team.

        Best regards,

        © rabboni
        eLibrary Developer
        National Prayer Department
        """
    return Message(subject, recipients=[email], body=body)
