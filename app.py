from flask import Flask,render_template,request,flash,redirect,url_for,session,logging

from flask_mysqldb import  MySQL
from wtforms import Form ,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps



app = Flask(__name__)

#config mysql
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='myflaskapp'
app.config['MYSQL_CURSORCLASS']='DictCursor'

#initialize mysql

mysql= MySQL(app)


@app.route('/')
def index():
    return render_template('home.html')



@app.route('/about')
def about():
    return render_template('about.html')
#check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash("unauthorised, please login","danger")
            return redirect(url_for("login"))
    return wrap




@app.route('/goals')
@is_logged_in
def goals():
    # create cursor
    username = session['username']
    cur = mysql.connection.cursor()

    # get goals
    result = cur.execute("SELECT * FROM goals WHERE author=%s",[username])
    goals = cur.fetchall()

    if result > 0:
        return render_template("goals.html", goals=goals)
    else:
        msg = "You have not  posted any goals currently."
        return render_template("goals.html", msg=msg)
    # close connection

    cur.close()

@app.route('/goal/<string:id>/')
@is_logged_in
def goal(id):
    #take id make query and then pass it to the view
    #create cursor
    cur= mysql.connection.cursor()

    #get goal

    result=cur.execute("SELECT * FROM goals WHERE id=%s",[id])

    #we only fetching one single goal from db
    goal=cur.fetchone()
    return render_template('goal.html', goal=goal)

class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min=1,max=50)])
    username= StringField('Username',[validators.Length(min=4,max=25)])
    email=StringField('Email',[validators.Length(min=6,max=50)])
    password =PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm',message='password do not match')
    ])
    confirm=PasswordField('Confirm Password')

@app.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm(request.form)
    if request.method=='POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password= sha256_crypt.encrypt(str(form.password.data))
        #password= form.password.data

        #create cursor

        cur=mysql.connection.cursor()

        #execute query
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s) ",(name,email,username,password))
        #commit to db

        mysql.connection.commit()

        #close connection
        cur.close()

        flash("You are now registered and can log in","success")
        return redirect(url_for('login'))


        #return render_template('register.html',form=form)

    return render_template('register.html',form=form)

#user login

@app.route('/login',methods=['GET','POST'])
def login():
    global username
    if request.method == 'POST':

        #get form fields

        username=request.form['username']
        password_candidate=request.form['password']

        #create cursor

        cur=mysql.connection.cursor()

        #get user by username

        result=cur.execute("SELECT * FROM users WHERE username =%s ",[username])

        if result > 0:

            #get the stored password

            data=cur.fetchone()
            password=data['password']

            #compare the passwords
            if sha256_crypt.verify(password_candidate,password):

                session['logged_in']=True
                session['username']=username

                flash("you are now logged in",'success')
                return redirect(url_for('dashboard'),)



                #error = 'valid login credentials'
                #return render_template('login.html', error=error)
                #app.logger.info('PASSWORD MATCHED')
            else:
                error='invalid login credentials'
                return render_template('login.html',error=error)

            #close connection

            cur.close()
        else:
            error="User not found,try registering first then log in"

            return render_template('login.html',error=error)

    return render_template('login.html')




#logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@is_logged_in
def dashboard():
    #create cursor
    username=session['username']
    cur=mysql.connection.cursor()

    #get goals

    result=cur.execute("SELECT * FROM goals WHERE author=%s",[username])
    goals = cur.fetchall()

    if result>0:
        return render_template("dashboard.html",goals=goals)
    else:
        msg= "You have not posted any goals Yet"
        return render_template("dashboard.html",msg=msg)
    #close connection

    cur.close()









    return render_template('dashboard.html')









class GoalForm(Form):
    title = StringField('Title',[validators.Length(min=1,max=200)])
    body= TextAreaField('Body',[validators.Length(min=30)])

#add goal
@app.route('/add_goal',methods=['GET','POST'])
@is_logged_in
def add_goal():

    form=GoalForm(request.form)
    if request.method=='POST' and form.validate():
        title=form.title.data
        body=form.body.data

        #create cursor
        cur= mysql.connection.cursor()

        #execute
        cur.execute("INSERT INTO goals(title,body,author) VALUES(%s,%s,%s)",(title,body,session['username']))

        #commit
        mysql.connection.commit()

        #close connection


        cur.close()

        #send flash message

        flash('Goals added','success')

        return redirect(url_for('dashboard'))
    return  render_template('add_goal.html',form=form)



#edit  goal
@app.route('/edit_goal/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_goal(id):
    #create cursor
    cur=mysql.connection.cursor()

    #get goalposted by id

    result=cur.execute("SELECT * FROM goals WHERE id=%s",[id])

    goal=cur.fetchone()


    #get form
    form=GoalForm(request.form)

    #populate fields

    form.title.data=goal['title']
    form.body.data=goal['body']

    if request.method=='POST' and form.validate():
        title=request.form['title']

        body=request.form['body']

        #create cursor
        cur= mysql.connection.cursor()

        # update then execute
        cur.execute("UPDATE goals SET title=%s, body=%s WHERE id=%s",(title,body,id))

        #commit
        mysql.connection.commit()

        #close connection


        cur.close()

        #send flash message

        flash('Goal Updated','success')

        return redirect(url_for('dashboard'))
    return  render_template('edit_goal.html',form=form)


#delete goal
@app.route('/delete_goal/<string:id>', methods=['post'])
@is_logged_in
def delete_goal(id):
    #create cursor
    cur= mysql.connection.cursor()

    #execute
    cur.execute("DELETE FROM goals WHERE id=%s",[id])

    #commit
    mysql.connection.commit()

    #close connection
    cur.close()

    #flash message then redirect
    flash("Goal deleted", 'success')

    return redirect(url_for('dashboard'))





if __name__=='__main__':
    app.secret_key='secret123'
    app.run(debug=True)