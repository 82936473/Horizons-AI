from flask import Flask, render_template,request,redirect,url_for,session,flash
from datetime import date
from functools import wraps
from database import db
from sqlalchemy import case 
from werkzeug.security import generate_password_hash, check_password_hash
import os
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")
app.secret_key="Long_random_secret_key"
tasks=None
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///horizons.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# db = SQLAlchemy()
db.init_app(app)
from models import CompletedTask, User,Task
with app.app_context():
    db.create_all()

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("log_in"))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html',title='Home')


@app.route('/sign_up',methods=['POST','GET'])
def sign_up():
    if "user_id" in session:
         return redirect(url_for("dashboard"))
    error=None
    if request.method=='POST':
        username = request.form.get("username")
        password = request.form.get("password")
        verify = request.form.get("verifypassword")
        try:
            if password != verify:
                raise ValueError("Password do not match")
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                raise ValueError("Username already exists")
            new_user = User(username=username,password=generate_password_hash(password))  #!#!
            db.session.add(new_user)
            db.session.commit()
            session["user_id"]=new_user.id
            session["username"]=new_user.username
            return redirect(url_for('dashboard'))
        except ValueError as e:
            error=str(e)
    return render_template('sign_up.html',title='Sign up',error=error)


@app.route('/log_in',methods=['POST','GET'])
def log_in():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    error=None
    if request.method=='POST':
        username = request.form.get("username")
        password = request.form.get("password")
        try:
            user = User.query.filter_by(username=username).first()
            if user is None or not check_password_hash(user.password, password):
                raise ValueError("Incorrect Username or Password")
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("dashboard"))
        except ValueError as e:
            error=str(e)
    return render_template('log_in.html',title='Log in',error=error)


@app.route("/dashboard")
@login_required
def dashboard():
    sort = request.args.get("sort", "date")
    query = Task.query.filter_by(user_id=session["user_id"])
    if sort == "priority":
        query = query.order_by(case((Task.priority == "High", 1),(Task.priority == "Medium", 2),(Task.priority == "Low", 3),))
    elif sort == "name":
        query = query.order_by(Task.title)
    else:
        query = query.order_by(Task.due_date)
    tasks = query.all()

    return render_template("dashboard.html",title="Dashboard",tasks=tasks,status="dashboard")
@app.route("/add", methods=["GET", "POST"])
@login_required
def add_task():
    if request.method == "POST":
        try:
            task = request.form["task"]
            priority = request.form["priority"]
            due_date = request.form["due_date"]
            user_id=session["user_id"]
            if due_date:
                due_date=date.fromisoformat(due_date)
            else:
                due_date=None
            new_task = Task(title=task,priority=priority,due_date=due_date if due_date else None,user_id=user_id)
            db.session.add(new_task)
            db.session.commit()
            flash("Task added successfully!", "success")
        except Exception:
            flash("Something went wrong", "error")
        return redirect(url_for("dashboard"))

    return render_template("add_task.html",status="add_task",title="Add Task")

@app.route('/edit/<int:task_id>', methods=['GET','POST'])
@login_required
def edit_task(task_id):
    task=Task.query.filter_by(id=task_id,user_id=session["user_id"]).first_or_404()
    if request.method=="POST":
        try:
            task.title=request.form["task"]
            task.priority=request.form['priority']
            due_date=request.form['due_date']
            if due_date:
                from datetime import date
                task.due_date = date.fromisoformat(due_date)
            else:
                task.due_date = None
            db.session.commit()
            flash("Task updated successfully!", "success")
        except Exception:
            flash("Something went wrong", "error")
        print(f"------------------------------------------------------{task_id}------------------------------------------------------") ##!#!#!#!#!
        return redirect(url_for("dashboard"))
    return render_template("edit_task.html", task=task)


@app.route('/delete/<int:task_id>/<source>/<status>')
@login_required
def delete_task(task_id, source,status):
    if source=='None':
        try:
            task=Task.query.filter_by(id=task_id,user_id=session["user_id"]).first_or_404()
            db.session.delete(task)
            db.session.commit()
            if status=="complete":
                flash("Task completed!", "success")
            elif status=="None":
                flash("Task deleted successfully!", "success")
        except Exception:
            flash("Something went wrong", "error")
        return redirect(url_for("dashboard"))
    elif source=='completed_source':
        try:
            task=CompletedTask.query.filter_by(id=task_id,user_id=session["user_id"]).first_or_404()
            db.session.delete(task)
            db.session.commit()
            flash("Task deleted successfully!", "success")
        except Exception:
            flash("Something went wrong", "error")
        return redirect(url_for("completed_tasks"))
    

@app.route('/delete_all/<source>')
@login_required
def delete_all_tasks(source):
    if source=='None':
        try:
            Task.query.filter_by(user_id=session["user_id"]).delete()
            db.session.commit()
            flash("All tasks deleted successfully!", "success")
        except Exception:
            flash(f"Something went wrong", "error")
        return redirect(url_for("dashboard"))
    elif source=='completed_source':
        try:
            CompletedTask.query.filter_by(user_id=session["user_id"]).delete()
            db.session.commit()
            flash("All tasks deleted successfully!", "success")
        except Exception:
            flash("Something went wrong", "error")
        return redirect(url_for("completed_tasks"))

@app.route('/complete/<int:task_id>/<task_title>/<due_date>')
@login_required
def complete_task(task_id,task_title,due_date):
    task = task_title
    due_date = due_date
    if due_date!='None':
            due_date=date.fromisoformat(due_date)
    else:
            due_date=None
    completed_task = CompletedTask(title=task,due_date=due_date,user_id=session["user_id"])
    db.session.add(completed_task)
    db.session.commit()
    return redirect(url_for("delete_task", task_id=task_id, source='None', status="complete"))


@app.route('/completed')
@login_required
def completed_tasks():
    tasks = CompletedTask.query.filter_by(user_id=session["user_id"]).all()
    return render_template("completed.html", title="Completed Tasks", tasks=tasks, status="completed_tasks")


@app.route("/logout")
def logout():
    if "user_id" not in session:
         return redirect(url_for("log_in"))
    session.clear()
    return redirect(url_for("home"))
with app.app_context():
    db.create_all()
if __name__ == "__main__":
    app.run(debug=True)