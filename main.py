from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
import re

app = Flask(__name__)
app.config['DEBUG'] = True
# Note: the connection string after :// contains the following info:
# user:password@server:portNumber/databaseName

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:St2rcoder@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key ="mrfwkdmsfksdlmsdkl5msdak82u4248u2nlmdakam"

class Blog(db.Model):
    
    #Define fields in the Blog table 
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(500))
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    
    #Constructor for the Blog class
    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship("Blog", backref="owner")

    def __init__(self, email, password):
        self.email =email
        self.password = password



@app.route('/')
def index():

    return redirect("/blog")

#route for displaying a list of blog entries
@app.route('/blog')
def blog_list():
    #Retrieve query arguments for the url if the user was redirected here.
    blog_id = request.args.get("id")

    # if the url contain query arguments, display the log entry associated with the id 
    # in the query argument
    if(blog_id):
        blog_id = int(blog_id)
        blog = Blog.query.filter_by(id=blog_id).first()
        return render_template('blog-entry.html', title="Blog Entry", blog=blog)
    else:
        #show all blog entries in asending order 
        #blogs = Blog.query.all()

        #show all blog entries in desending order 
        blogs = Blog.query.order_by((desc(Blog.id))).all()

        return render_template('blog-listing.html', title="Blog List", blogs=blogs)

#route for redirecting to the login page
@app.before_request
def require_login():
    allowed_routes = ['login', 'signup']
    if (request.endpoint not in allowed_routes) and ('email' not in session):
        return redirect("/login")

#route for the login page
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if (user and user.password == password):
            session['email'] = email
            flash("Logged in")
            return redirect("/")
        else:
            flash("Password incorrect or user doesn't exsist.", "error")

    return render_template('login.html',title="login", email="")

#route for signing up for new account 
@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        #get form data
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']

        #initialize error messages
        pass_error = False
        match_error = False
        email_error = False
        error_query = ""
    
        #Regular expression used for email validation 
        regex = re.compile(r"[\w-]+@[\w-]+\.\w+")
    
        if (password == ""):
            # the user tried to enter an invalid password,
            # so we redirect back to the front page and tell them what went wrong
            flash("Please enter a valid password.", "error")
            pass_error = True
        elif(len(password) < 3) or (len(password) > 20) or (" " in password):
            flash("The password must be 3-20 characters and can't contain spaces", "error")
            pass_error = True
        if (verify == "") or (password != verify):
            # the two passwords didn't match,
            # so we redirect back to the front page and tell them what went wrong
            flash("The passwords did not match", "error")
            match_error = True
        if(email != ""):  #The email field can be left blank
            valid_email = regex.match(email) #does the email match the regular expression. 
            if(len(email) < 3) or (len(email) > 20) or (not valid_email):
                # the user tried to enter an invalid email address,
                # so we redirect back to the front page and tell them what went wrong
                flash("The email must be 3-20 characters, must contain a single '@' and a single '.', and can't contain spaces",
                "error")
                email_error = True
        
        if (email_error):
            error_query += "&eerror=" + str(email_error)
    
        if (pass_error):
            error_query += "&perror=" + str(pass_error)

        if (match_error):
            error_query += "&merror=" + str(match_error)

        if (error_query != ""):
            # redirect to homepage, and include error as a query parameter in the URL.
            return redirect("/signup?email=" + email + error_query)
        else:    
            # if we didn't redirect by now, then all is well
            exsisting_user = User.query.filter_by(email=email).first()
        
            if (not (exsisting_user)):
                new_user = User(email, password)
                db.session.add(new_user)
                db.session.commit()
            
                return redirect("/login")
            else:
                flash("That user already exsist", "error")
    else:
        #Retrieve query arguments for the url if the user was redirected here.
        email = request.args.get("email")
        perror = bool(request.args.get("perror"))
        merror = bool(request.args.get("merror"))
        eerror = bool(request.args.get("eerror"))

        #If the email aren't sent as query parameters the previous statements set to None.
        #In that case, it needs to be set to empty strings.
        if email == None:
            email = ""

        #display the signup form.
        return render_template("signup.html", title="User Signup", email=email, perror=perror, merror=merror, eerror=eerror)

#route for displaying the form to add a new blog entry.
@app.route('/new-post')
def new_post():
    #Retrieve query arguments for the url if the user was redirected here.
    btitle = request.args.get("btitle")
    text = request.args.get("bbody")
    terror = request.args.get("terror")
    berror = request.args.get("berror")

    #If the title and body aren't sent as query parameters the previous statements set to None.
    #In that case, they need to be set to empty strings.
    if btitle == None:
        btitle = ""
    if text == None:
        text = ""

    #display the new-post form.
    return render_template("new-post.html", title="Add a new Blog entry", blog_title=btitle, blog_post=text, terror=terror, berror=berror)

#route for processing the form to add a new blog entry.
@app.route('/add-entry', methods=['POST'])
def add_entry():

    #get info from the form.
    blog_name = request.form['blog_title']
    blog_text = request.form['blog_text']

    #initialize error messages
    title_error = ""
    body_error = ""
    error_query = ""
    
    if (blog_name == ""):
        # the user tried to enter a blank blog title
        # so we redirect back to the form page and tell them what went wrong
        title_error = "Please enter title for your blog entry."
    
    if (blog_text == ""):
        # the user tried to enter a blank post body,
        # so we redirect back to the form page and tell them what went wrong
        body_error = "Please enter the body of your blog entry."

    if (title_error != ""):
            error_query += "&terror=" + title_error

    if (body_error != ""):
            error_query += "&berror=" + body_error

    if (error_query != ""):
        # redirect to homepage, and include error as a query parameter in the URL.
        return redirect("/new-post?btitle=" + blog_name + "&bbody=" + blog_text + error_query)
    else:    
        # if we didn't redirect by now, then all is well

        owner = User.query.filter_by(email=session['email']).first()
        #Add new blog entry to the database
        new_blog = Blog(blog_name, blog_text, owner)
        db.session.add(new_blog)
        db.session.commit()
        
        #Use Case 1
        #return to the list of all blog entries
        #return redirect("/blog")

        #Use Case 2
        #Show the new blog entry

        blog_id = str(new_blog.id)
        return redirect("/blog?id=" + blog_id)

@app.route("/logout")
def logout():
    del session['email']
    return redirect("/")

if __name__ == "__main__":
    app.run()