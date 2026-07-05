from flask import Flask, render_template,request,redirect,url_for,session,flash
from datetime import date
from functools import wraps
from database import db
from sqlalchemy import case 
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from ai_models import TaskBreakdown, TaskDecision
import ast
import os
app = Flask(__name__)
load_dotenv()
app.secret_key = os.environ.get("SECRET_KEY")
tasks=None
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///horizons.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
from models import CompletedTask, User, Task, AISuggestions, SubTask
with app.app_context():
    db.create_all()

decision_maker=TaskDecision()
breaker=TaskBreakdown()
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
            new_user = User(username=username,name='',password=generate_password_hash(password))  #!#!
            db.session.add(new_user)
            db.session.commit()
            session["user_id"]=new_user.id
            session["username"]=new_user.username
            return redirect(url_for('user_name'))
        except ValueError as e:
            error=str(e)
    return render_template('sign_up.html',title='Sign up',error=error)

@app.route('/user_name',methods=['POST','GET'])
def user_name():
    if request.method=='POST':
        name=request.form.get("name")
        user = User.query.filter_by(id=session["user_id"]).first_or_404()
        user.name=name
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template("user's_name.html")


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
    user = User.query.get(session["user_id"])
    if user is None:
        session.clear()
        return redirect(url_for("login"))
    name=user.name
    query = Task.query.filter_by(user_id=session["user_id"])
    if sort == "priority":
        query = query.order_by(case((Task.priority == "High", 1),(Task.priority == "Medium", 2),(Task.priority == "Low", 3),))
    elif sort == "name":
        query = query.order_by(Task.title)
    else:
        query = query.order_by(Task.due_date)
    tasks = query.all()
    return render_template("dashboard.html",title="Dashboard",tasks=tasks,status="dashboard",name=name)
@app.route("/add", methods=["GET", "POST"])
@login_required
def add_task():
    user = User.query.get(session["user_id"])
    name=user.name
    if request.method == "POST":
        try:
            task = request.form["task"]
            priority = request.form["priority"]
            due_date = request.form["due_date"]
            category= request.form["category"]
            user_id=session["user_id"]
            evaluate=decision_maker.evaluate_task(task)
            if not category:
                category=None
            if evaluate=="yes":
                evaluate=True
            else :
                evaluate=False
            if due_date:
                due_date=date.fromisoformat(due_date)
            else:
                due_date=None
            new_task = Task(title=task,priority=priority,due_date=due_date,user_id=user_id,category=category,evaluate=evaluate)
            db.session.add(new_task)
            db.session.commit()
            flash("Task added successfully!", "success")
        except :
            flash(f"Something went wrong", "error")
            db.session.rollback()
        return redirect(url_for("dashboard"))
    return render_template("add_task.html",title="Add Task",name=name,submit_url=url_for('add_task'))

@app.route('/add_subtask/<task_id>',methods=["POST",'GET'])
@login_required
def add_subtask(task_id):
    user = User.query.get(session["user_id"])
    name=user.name
    if request.method=="POST":
        try:
            task = request.form["task"]
            priority = request.form["priority"]
            due_date = request.form["due_date"]
            category= request.form["category"]
            user_id=session["user_id"]
            if not category:
                category=None
            if due_date:
                due_date=date.fromisoformat(due_date)
            else:
                due_date=None
            new_subtask = SubTask(parent_id=task_id,title=task,priority=priority,category=category,due_date=due_date,user_id=user_id)
            db.session.add(new_subtask)
            db.session.commit()
            flash('Tasks added successfully!','success')
        except:
            flash(f"Something went wrong", "error")
            db.session.rollback()
        return redirect(url_for('dashboard'))
    return render_template("add_task.html",title="Add SubTask",name=name,submit_url=url_for("add_subtask",task_id=task_id))

@app.route('/edit/<int:task_id>', methods=['GET','POST'])
@login_required
def edit_task(task_id):
    user = User.query.get(session["user_id"])
    name=user.name
    task=Task.query.filter_by(id=task_id,user_id=session["user_id"]).first_or_404()
    if request.method=="POST":
        try:
            updated_task=request.form["task"]
            task.title=updated_task
            task.priority=request.form['priority']
            task.category=request.form['category']
            due_date=request.form['due_date']
            if due_date:
                from datetime import date
                task.due_date = date.fromisoformat(due_date)
            else:
                task.due_date = None
            evaluate=decision_maker.evaluate_task(updated_task)
            if evaluate=="yes":
                evaluate=True
            else :
                evaluate=False
            task.evaluate=evaluate
            db.session.commit()
            flash("Task updated successfully!", "success")
        except Exception:
            flash("Something went wrong", "error")
            db.session.rollback()
        return redirect(url_for("dashboard"))
    return render_template("edit_task.html", task=task,name=name,submit_url=url_for('edit_task',task_id=task.id))

@app.route('/edit_suggestion_task/<task_id>/<_id_>',methods=['POST','GET'])
@login_required
def edit_suggestion_task(task_id,_id_):
    user = User.query.get(session["user_id"])
    name=user.name
    task=AISuggestions.query.filter_by(id=task_id,user_id=session["user_id"]).first_or_404()
    if request.method=="POST":
        try:
            task.title=request.form["task"]
            task.priority=request.form['priority']
            task.category=request.form['category']
            due_date=request.form['due_date']
            if due_date:
                from datetime import date
                task.due_date = date.fromisoformat(due_date)
            else:
                task.due_date = None
            db.session.commit()
            flash("Task updated successfully!", "success")
            tasks=AISuggestions.query.filter_by(user_id=session["user_id"])
        except Exception:
            flash("Something went wrong", "error")
            db.session.rollback()
        return render_template("ai_suggestions.html",title="suggestions",tasks=tasks,id=_id_,name=name)
    return render_template("edit_task.html", task=task, id=_id_,name=name,submit_url=url_for('edit_suggestion_task',task_id=task.id,_id_=_id_))

@app.route('/edit_subtask/<subtask_id>',methods=['POST','GET'])
@login_required
def edit_subtask(subtask_id):
    user = User.query.get(session["user_id"])
    name=user.name
    subtask=SubTask.query.filter_by(id=subtask_id,user_id=session["user_id"]).first_or_404()
    if request.method=="POST":
        try:
            subtask.title=request.form["task"]
            subtask.priority=request.form['priority']
            subtask.category=request.form['category']
            due_date=request.form['due_date']
            if due_date:
                from datetime import date
                subtask.due_date = date.fromisoformat(due_date)
            else:
                subtask.due_date = None
            db.session.commit()
            flash("Task updated successfully!", "success")
        except Exception:
            flash("Something went wrong", "error")
            db.session.rollback()
        return redirect(url_for('dashboard'))
    return render_template("edit_task.html", task=subtask,name=name,submit_url=url_for('edit_subtask',subtask_id=subtask.id))

@app.route('/delete/<int:task_id>/<status>')
@login_required
def delete_task(task_id,status):
    user = User.query.get(session["user_id"])
    name=user.name
    try:
        task=Task.query.filter_by(id=task_id,user_id=session["user_id"]).first_or_404()
        db.session.delete(task)
        db.session.commit()
        if status=="complete":
            flash("Task completed!", "success")
        elif status=="None":
            flash("Task deleted successfully!", "success")
            db.session.rollback()
        return redirect(url_for("dashboard"))
    except:
        flash("Something went wrong", "error")

@app.route("/delete_suggestion_task/<int:task_id>/<_id_>")
@login_required
def delete_suggestion_task(task_id,_id_):
    user = User.query.get(session["user_id"])
    name=user.name
    try:
        task = AISuggestions.query.filter_by(id=task_id, user_id=session["user_id"]).first_or_404()
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted successfuly!", "success")
    except Exception:
        flash("Something went wrong.", "error")
        db.session.rollback()
    return render_template("ai_suggestions.html",title="suggestions",tasks=tasks,id=_id_,name=name)


@app.route("/delte_completed_task/<int:task_id>")
@login_required
def delete_completed_task(task_id):
    try:
        task = CompletedTask.query.filter_by(id=task_id, user_id=session["user_id"]).first_or_404()
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted successfuly!", "success")
    except Exception:
        flash("Something went wrong.", "error")
        db.session.rollback()
    return redirect(url_for("completed_tasks"))

@app.route("/delete_subtask/<int:subtask_id>")
@login_required
def delete_subtask(subtask_id):
    try:
        subtask = SubTask.query.filter_by(id=subtask_id, user_id=session["user_id"]).first_or_404()
        db.session.delete(subtask)
        db.session.commit()
        flash("Subtask deleted successfuly!", "success")
    except Exception:
        db.session.rollback()
        flash("Something went wrong.", "error")
        
    return redirect(url_for("dashboard"))

@app.route('/delete_all')
@login_required
def delete_all_tasks():
    try:
        Task.query.filter_by(user_id=session["user_id"]).delete()
        db.session.commit()
        flash("All tasks deleted successfully!", "success")
    except Exception:
        flash(f"Something went wrong", "error")
        db.session.rollback()
    return redirect(url_for("dashboard"))

@app.route('/delete_all_completed_tasks')
@login_required
def delete_all_completed_tasks():
    try:
        CompletedTask.query.filter_by(user_id=session["user_id"]).delete()
        db.session.commit()
        flash("All tasks deleted successfully!", "success")
    except Exception:
        flash("Something went wrong", "error")
        db.session.rollback()
    return redirect(url_for("completed_tasks"))

@app.route('/complete_task/<int:task_id>')
@login_required
def complete_task(task_id):
    try:
        task=Task.query.filter_by(id=task_id,user_id=session["user_id"]).first_or_404()
        title = task.title
        due_date = task.due_date
        completed_task = CompletedTask(title=title,due_date=due_date,user_id=session["user_id"])
        db.session.add(completed_task)
        db.session.commit()
    except Exception:
            flash("Something went wrong", "error")
            db.session.rollback()
    return redirect(url_for("delete_task", task_id=task_id,status="complete"))

@app.route('/complete_subtask/<int:subtask_id>')
@login_required
def complete_subtask(subtask_id):
    try:
        task=SubTask.query.filter_by(id=subtask_id,user_id=session["user_id"]).first_or_404()
        task = task.title
        due_date = task.due_date
        completed_task = CompletedTask(title=task,due_date=due_date,user_id=session["user_id"])
        db.session.add(completed_task)
        db.session.commit()
    except:
            flash("Something went wrong", "error")
            db.session.rollback()
    return redirect(url_for("delete_subtask", subtask_id=subtask_id))

@app.route('/completed')
@login_required
def completed_tasks():
    user = User.query.get(session["user_id"])
    name=user.name
    try:
        tasks = CompletedTask.query.filter_by(user_id=session["user_id"]).all()
    except:
        flash("Something went wrong", "error")
        db.session.rollback()
    return render_template("completed.html", title="Completed Tasks", tasks=tasks, status="completed_tasks",name=name)

@app.route('/break-down/<task>/<task_id>',methods=['GET','POST'])
@login_required
def break_down(task,task_id):
    user = User.query.get(session["user_id"])
    name=user.name
    try:
        new_tasks=ast.literal_eval(breaker.break_down_task(task))
        for i in new_tasks:
            new_task = AISuggestions(title=i[0],priority=i[1],category=i[2],due_date=None,user_id=session["user_id"])
            db.session.add(new_task)
            db.session.commit()
        breaked_tasks =AISuggestions.query.filter_by(user_id=session["user_id"]).all()
    except:
        flash('Something went wrong','error')
        db.session.rollback()
    return render_template("ai_suggestions.html",title="suggestions",tasks=breaked_tasks,id=task_id,name=name)

@app.route('/confirm-break-down/<task_id>')
@login_required
def confirm_break_down(task_id):
    try:
        suggestions = AISuggestions.query.filter_by(user_id=session["user_id"])
        for i in suggestions:
            new_task = SubTask(parent_id=task_id,title=i.title,priority=i.priority,category=i.category,due_date=i.due_date,user_id=session["user_id"])
            db.session.add(new_task)
            db.session.delete(i)
        Task.query.filter_by(user_id=session["user_id"],id=task_id).first_or_404().evaluate=False
        db.session.commit()
        flash('Tasks added successfully!','success')
    except Exception as e:
            print(f"------------------{e}")
            flash("Something went wrong", "error")
            db.session.rollback()
    return redirect(url_for('dashboard'))


@app.route('/cancel-break-down')
@login_required
def cancel_break_down():
    try:
        AISuggestions.query.filter_by(user_id=session["user_id"]).delete()
        db.session.commit()
    except:
        flash("Something went wrong", "error")
    return redirect(url_for('dashboard'))


@app.route("/logout")
def logout():
    if "user_id" not in session:
         return redirect(url_for("log_in"))
    session.clear()
    return redirect(url_for("home"))

#!#!#! reset the database if RESER_DB=="True", For your local using, you can just use:
#! with app.app_context():
#!    db.create_all()
with app.app_context():
    if os.environ.get("RESET_DB") == "True":
        print("Wiping and recreating the database...")
        db.drop_all()
        db.create_all()
        print("Database reset complete!")
    else:
        db.create_all()
if __name__ == "__main__":
    app.run(debug=True)