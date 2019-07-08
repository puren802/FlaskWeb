from flask import Flask,render_template,flash,redirect,url_for,session,request,logging
from flask_mysqldb import MySQL
from data import Articles
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

app=Flask(__name__)
app.debug=True

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
Articles = Articles()
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def afrticles():
    return render_template('articles.html',articles=Articles)


@app.route('/articles/<int:id>/')
def article(id):
    return render_template('article.html',id=id,articles=Articles)

class RegisterForm(Form):
        name=StringField('Name',[validators.Length(min=1,max=50)])
        username = StringField('Username',[validators.Length(min=4,max=25)])
        email = StringField('Email',[validators.Length(min=4,max=25)])
        password = PasswordField('Password', [ validators.DataRequired (),validators.EqualTo('confirm',message ='passwords do not match')])
        confirm = PasswordField('Confirm password')
        
@app.route('/register', methods=['GET','POST'])
def register():
        form = RegisterForm(request.form)
        if request.method == 'POST' and form.validate():
                name=form.name.data
                email=form.email.data
                username=form.username.data
                password=sha256_crypt.encrypt(str(form.password.data))
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",(name,email,username,password))
                mysql.connection.commit()
                cur.close()
                flash("You are now Registered and you can login",'success')
                redirect(url_for('login'))
        return render_template('register.html',form=form)

@app.route('/login', methods=['GET','POST'])
def login():
        if request.method == 'POST':
                username=request.form['username']
                password_candidate=request.form['password']
                cur = mysql.connection.cursor()
                result=cur.execute("SELECT * FROM users WHERE username=%s",[username])
                if result>0:
                        data=cur.fetchone()
                        password=data['password']

                        if sha256_crypt.verify(password_candidate,password):
                                session['logged_in'] = True
                                session['username'] = username

                                flash('You are now logged in','success')
                                return redirect(url_for('dashboard'))
                        else:
                                error = 'password not match'
                                return render_template('login.html',error=error)
                        cur.close()
                else:
                        error='Username not found'
                        return render_template('login.html',error=error)                
        return render_template('login.html')

def is_logged_in(f):
        @wraps(f)
        def wrap(*args,**kwargs):
                if 'logged_in' in session:
                        return f(*args, **kwargs)
                else:
                        flash('Unauthorized, please login','danger')
                return redirect(url_for('login'))
        return wrap

@app.route('/dashboard')
@is_logged_in
def dashboard():
        return render_template('dashboard.html')

@app.route('/logout')
def logout():
        session.clear()
        flash('you are now logged out','success')
        return redirect(url_for('login'))

@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
        form = ArticleForm(request.form)
        if request.method == 'POST' and form.validate():
                title = form.title.data
                body = form.body.data
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)",(title,body,session['username']))
                mysql.connection.commit()
                flash('Article created','success')
                return redirect(url_for('dashboard'))
        return render_template('add_article.html',form=form)

class ArticleForm(Form):
    title = StringField('Title',[validators.Length(min=1,max=50)])
    body = TextAreaField('Body',[validators.Length(min=30,max=1000)])


if __name__ =='__main__':
        app.secret_key='secret123'
        app.run()       