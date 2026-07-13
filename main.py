from flask import Flask, render_template,request,redirect,url_for,session,flash,make_response
from flask_mail import Mail, Message
from premailer import transform
from flask_apscheduler import APScheduler
from datetime import date,datetime,timezone,timedelta
from functools import wraps
from database import db
from sqlalchemy import case 
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from ai_models import AIModels
from email_validator import validate_email,EmailNotValidError
import json
import os
app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
load_dotenv()
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get("address_email")
app.config['MAIL_PASSWORD'] = os.environ.get("password_email")
app.secret_key = os.environ.get("SECRET_KEY")
mail=Mail()
mail.init_app(app)
tasks=None
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///horizons.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
from models import CompletedTask, User, Task, AISuggestions, SubTask
with app.app_context():
    db.create_all()
ai_models=AIModels()
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.headers.get("HX-Request"):
                response=make_response("",200)
                response.headers["HX-Redirect"] = url_for('log_in')
                return response
            return redirect(url_for("log_in"))
        return f(*args, **kwargs)
    return decorated_function

def purge_expired_tasks():
    expired_time=datetime.now(timezone.utc) - timedelta(hours=12)
    expired_completed_tasks=CompletedTask.query.filter(CompletedTask.user_id==session['user_id'],CompletedTask.completed_at<=expired_time)
    expired_completed_tasks.delete()
    db.session.commit()

def check_strong_password(password):
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    if not any(char.isupper() for char in password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not any(char.islower() for char in password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one number.")
    if not any(char in '@#$%!*&' for char in password):
        raise ValueError("Password must contain at least one special character (@, #, $, %, !, *, &).")
        
    return True

def insights(user):
    try:
        week_completed_tasks = user.weekly_completed_tasks #! return type 'int'
        total_completed_tasks = user.total_completed_tasks #! return type 'int' 
        average_completion_time = user.average_completion_time #! return type 'float' or 'str'
        if average_completion_time < 0.01666667: #! less than one minute
             average_completion_time = "In record time!"
        categories=user.categories.split(',')
        top_category = max(categories) #! return type 'str'
        count_priority_tasks = user.priorities #! return type {'high':num,'medium':num,'low':num}
        top_priority = max(count_priority_tasks)
        db.session.commit()
    except:
        db.session.rollback()
    return {"name":user.name,"Total completed tasks":total_completed_tasks,"Total completed tasks this week":week_completed_tasks,"Average completion time in hours":average_completion_time,"top category":top_category,"Count completed tasks by priority":count_priority_tasks,'top priority':top_priority}

scheduler = APScheduler()
@scheduler.task('cron', id='weekly_insights_reset', day_of_week='sun', hour=23, minute=59)
def weekly_static():
    with app.app_context():
        users=User.query.all()
        for user in users:
            try:
                statics=insights(user)
                ai_email=ai_models.static_generator_message(statics)
                email= render_template('weekly_static_table.html', static=statics, ai_output=ai_email)
                message = Message(subject='Your Horizons AI weekly summary', sender="ayman.laa09@gmail.com",recipients=[user.username])
                email=transform(email)
                message.html = email
                print(message)
                mail.send(message)
                user.weekly_completed_tasks = 0
                user.priorities = {'high':0,'medium':0,'low':0}
                user.categories = ''
                user.average_completion_time = 0.0
                db.session.commit()
            except:
                db.session.rollback()
scheduler.init_app(app)
scheduler.start()

#!#! change demo url
def greating_email(user_email,name):
    greating_email=f'''<p>Hi {name},</p>
    <p>Welcome to <strong>Horizons AI</strong>! 🚀 Your new personal command center for organizing your tasks and staying productive.<p>
    <p>Your account is officially ready✅. Here is what you can do <strong>right out of the gate</strong>:<p>
    <ul>
        <li>📝 <strong>Organize Your Tasks: Add your tasks, tag their priority levels, and categorize them to keep your workflow clean.</strong></li>
        <li>📊 <strong>Track Your Progress: Every task you check off feeds into your dashboard metrics.</strong></li>
        <li>📈 <strong>Unlock Weekly Insights: Our background system calculates your stats every single week, showing you your average completion times and top categories.</strong></li>
        <li>🤖 <strong>Enjoy you journey powered by AI.</strong></li>
    </ul>
    <p>👉 The board is clear and ready for your first task.<strong><a href="http://127.0.0.1:5000/dashboard" style="color: #007bff; font-weight: bold; text-decoration: underline;">Log in and start achieving your goals</a></strong></p>
    <p>Happy organizing,<br>
    <strong>The Horizons AI Team.</strong>🌟</p>
    '''
    message = Message(subject='WELCOME TO HORIZONS AI!',sender='ayman.laa09@gmail.com',recipients=[user_email])
    message.html = greating_email
    mail.send(message)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',title='404'), 404

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
        try:
            username = request.form.get("username")
            password = request.form.get("password")
            verify = request.form.get("verifypassword")
            email = validate_email(username, check_deliverability=True)
            valid_email = email.normalized
            check_strong_password(password)
            if password != verify:
                raise ValueError("Password do not match")
            existing_user=User.query.filter_by(username=valid_email).first()
            if existing_user:
                raise ValueError('An account with this email address already exists.')
            new_user = User(username=valid_email,name='',password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            session["user_id"]=new_user.id
            session["username"]=new_user.username
            purge_expired_tasks()
            return redirect(url_for('user_name'))
        except (ValueError,EmailNotValidError) as e:
            error=str(e)
    return render_template('sign_up.html',title='Sign up',error=error)

@app.route('/user_name',methods=['POST','GET'])
def user_name():
    if request.method=='POST':
        name=request.form.get("name")
        user = User.query.filter_by(id=session["user_id"]).first_or_404()
        user.name=name
        greating_email(user.username,name)
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
                raise ValueError("Invalid Email or Password")
            session["user_id"] = user.id
            session["username"] = user.username
            purge_expired_tasks()
            return redirect(url_for("dashboard"))
        except ValueError as e:
            error=str(e)
    return render_template('log_in.html',title='Log in',error=error)


@app.route("/dashboard")
@login_required
def dashboard():
    sort = request.args.get("sort", "date")
    user = User.query.filter_by(id=session["user_id"]).first()
    if user is None:
        session.clear()
        return redirect(url_for("log_in"))
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
            evaluate=ai_models.evaluate_task(task)
            if not category:
                category=ai_models.determinate_category(task)
                if category=='None':
                    category=None
            if evaluate=="yes":
                evaluate=True
            else :
                evaluate=False
            if due_date:
                due_date=date.fromisoformat(due_date)
            else:
                due_date=None
            new_task = Task(title=task,priority=priority,due_date=due_date,user_id=user_id,category=category,evaluate=evaluate,created_at=datetime.now(timezone.utc))
            db.session.add(new_task)
            db.session.commit()
            flash("Task added successfully!", "success")
        except :
            flash(f"Something went wrong", "error")
            db.session.rollback()
        return redirect(url_for("dashboard"))
    return render_template("add_task.html",title="Add Task",name=name,status='add_task',submit_url=url_for('add_task'))

#!#! need flash and finishing
@app.route('/quickadd',methods=['POST'])
@login_required
def quickadd():
    try:
        remaining=Task.query.filter_by(user_id=session['user_id']).count()
        prompt=request.form.get('quickadd_prompt')
        tasks=ai_models.quick_add(prompt)
        created_tasks=[]
        for task in tasks:
            title=task['task']
            priority=task['priority']
            category=task['category']
            due_date=task['due_date']
            user_id=session['user_id']
            if title=='None':
                return ''
            if category=='None':
                category=None
            if due_date=='None':
                due_date=None
            else:
                due_date=date.fromisoformat(due_date)
            new_task=Task(user_id=user_id,title=title, priority=priority, due_date=due_date, category=category,created_at=datetime.now(timezone.utc))
            db.session.add(new_task)
            for subtask in task.get("subtasks", []):
                subtask_title=subtask['subtask']
                subtask_priority=subtask['priority']
                subtask_due_date=subtask['due_date']
                if subtask_due_date=='None':
                    subtask_due_date=None
                else:
                    subtask_due_date=date.fromisoformat(subtask_due_date)
                new_subtask=SubTask(user_id=user_id,parent_task=new_task,title=subtask_title,priority=subtask_priority,due_date=subtask_due_date)
                db.session.add(new_subtask)
            db.session.add(new_task)
            hh_tasks=Task.query.filter_by(user_id=session['user_id']).all()
            created_tasks.append(new_task)
        db.session.commit()
        html_response=''
        if remaining==0:
            html_response+=f'''
            <div class="toolbar">
                <h3>Tasks</h3>
                <div class="dropdown">
                    <button class="menuu sortby"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M120-240v-80h240v80H120Zm0-200v-80h480v80H120Zm0-200v-80h720v80H120Z"/></svg><span>Sort by</span></button>
                    <div class="dropdown-content">
                        <a href="{ url_for('dashboard', sort='priority') }">Priority</a>
                        <a href="{ url_for('dashboard', sort='date') }">Due date</a>
                        <a href="{ url_for('dashboard', sort='name') }">Alphabetical</a>
                    </div> 
                </div>
            </div>
            <div class="delete-all-tasks">
                <a href="{ url_for('delete_all_tasks') }"  onclick="return confirm('Are you sure you want to delete all your tasks?')"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="m376-300 104-104 104 104 56-56-104-104 104-104-56-56-104 104-104-104-56 56 104 104-104 104 56 56Zm-96 180q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520Zm-400 0v520-520Z"/></svg><span>delete all tasks</span></a>
            </div>'''
        for task in created_tasks:
            html_response += f"<div class='task-card {task.priority.lower()}' id='task-{task.id}'><div class='card-header'><div>"
            if task.due_date:
                html_response+=f"<p><strong>Due date: </strong>{task.friendly_date}</p>"
            if task.category:
                html_response+=f"<p><strong>Category: </strong>{task.category}</p>"
            html_response+=f" <p><strong>Priority: </strong><span>{task.priority}</span></p></div>"
            html_response+=f'''<div class='dropdown'><button class='menuu'>⋮</button>
                            <div class='dropdown-content'>
                            <a href="{ url_for('edit_task', task_id=task.id) }"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M200-200h57l391-391-57-57-391 391v57Zm-80 80v-170l528-527q12-11 26.5-17t30.5-6q16 0 31 6t26 18l55 56q12 11 17.5 26t5.5 30q0 16-5.5 30.5T817-647L290-120H120Zm640-584-56-56 56 56Zm-141 85-28-29 57 57-29-28Z"/></svg><span>Edit</span></a>
                            <a hx-post="{ url_for('complete_task',task_id=task.id) }" hx-target="#task-{task.id}" hx-swap="delete swap:200ms" class=""><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M382-240 154-468l57-57 171 171 367-367 57 57-424 424Z"/></svg><span>Complete</span></a>
                            <a href="{ url_for('add_subtask',task_id=task.id) }"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="m560-120-57-57 144-143H200v-480h80v400h367L503-544l56-57 241 241-240 240Z"/></svg><span>Add Subtask</span></a>
                            <a hx-delete="{ url_for('delete_task', task_id=task.id) }" hx-target="#task-{task.id}" hx-swap="delete swap:200ms"  hx-confirm="Are you sure you want to delete this task?" class="" ><svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24"><path d="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360Z"/></svg><span>Delete</span></a></div></div></div><hr>
                '''
            html_response+=f"<div class='task-title'><p>{task.title}</p>"
            if task.subtasks:
                html_response+='<button class="toggle-arrow collapsed" onclick="toggleSubtasks(this)"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M480-528 296-344l-56-56 240-240 240 240-56 56-184-184Z"/></svg></button>'
            html_response+='</div></div>'
            html_response+=f'''<ul class="subtask-tree hide-subtasks" id="subtasks-{task.id}">'''
            for  subtask in task.subtasks:
                html_response+=f'''<li><div class="task-card {subtask.priority.lower()} id="task-{subtask.id}"><div class="card-header"><div>'''
                if subtask.due_date:
                    html_response+=f"<p><strong>Due date:</strong> { subtask.friendly_date }</p>"
                if subtask.category:
                    html_response+=f"<p><strong>Category: </strong>{ subtask.category }</p>"
                html_response+=f"<p><strong>Priority: </strong><span>{ subtask.priority }</span></p></div>"
                html_response+=f'''<div class="dropdown"><button class="menuu">⋮</button>
                <div class="dropdown-content">
                <a href="{ url_for('edit_subtask', subtask_id=subtask.id) }"><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M200-200h57l391-391-57-57-391 391v57Zm-80 80v-170l528-527q12-11 26.5-17t30.5-6q16 0 31 6t26 18l55 56q12 11 17.5 26t5.5 30q0 16-5.5 30.5T817-647L290-120H120Zm640-584-56-56 56 56Zm-141 85-28-29 57 57-29-28Z"/></svg><span>Edit</span></a>
                <a hx-post="{ url_for('complete_subtask',subtask_id=subtask.id) }" hx-target="#task-{ subtask.id }" hx-swap="delete swap:200ms" class=""><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M382-240 154-468l57-57 171 171 367-367 57 57-424 424Z"/></svg><span>Complete</span></a>
                <a hx-delete="{ url_for('delete_subtask', subtask_id=subtask.id) }" hx-target="#task-{ subtask.id }" hx-swap="delete swap:200ms"  hx-confirm="Are you sure you want to delete this subtask?" class=""><svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24"><path d="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360Z"/></svg><span>Delete</span></a>
                </div></div></div><hr>'''
                html_response+=f'''<div class="task-title"><p>{ subtask.title }</p></div></div></li>'''
            html_response+='</ul>'
        return html_response,200
    except:
        db.session.rollback()
        return "",404


@app.route('/add_subtask/<task_id>',methods=["POST",'GET'])
@login_required
def add_subtask(task_id):
    user = User.query.get(session["user_id"])
    name=user.name
    if request.method=="POST":
        try:
            parent_task=Task.query.filter_by(user_id=session['user_id'],id=task_id).first_or_404()
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
            new_subtask = SubTask(parent_task=parent_task,title=task,priority=priority,category=category,due_date=due_date,user_id=user_id)
            db.session.add(new_subtask)
            db.session.commit()
            flash('SubTask added successfully!','success')
        except:
            flash(f"Something went wrong", "error")
            db.session.rollback()
        return redirect(url_for('dashboard'))
    return render_template("add_task.html",title="Add Subtask",name=name,submit_url=url_for("add_subtask",task_id=task_id))

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
            category=request.form['category']
            if not category:
                category =ai_models.determinate_category(updated_task)
                if category == 'None':
                    category=None
            task.category=category
            due_date=request.form['due_date']
            if due_date:
                from datetime import date
                task.due_date = date.fromisoformat(due_date)
            else:
                task.due_date = None
            if not task.subtasks:
                evaluate=ai_models.evaluate_task(updated_task)
                task.evaluate=False
                if evaluate=="yes":
                    task.evaluate=True
            db.session.commit()
            flash("Task updated successfully!", "success")
        except :
            flash("Something went wrong", "error")
            db.session.rollback()
        return redirect(url_for("dashboard"))
    return render_template("add_task.html", title='Edit Task',task=task,name=name,submit_url=url_for('edit_task',task_id=task.id))

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
    return render_template("add_task.html", title='Edit Task',task=task, id=_id_,name=name,submit_url=url_for('edit_suggestion_task',task_id=task.id,_id_=_id_))

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
            flash("Subtask updated successfully!", "success")
        except Exception:
            flash("Something went wrong", "error")
            db.session.rollback()
        return redirect(url_for('dashboard'))
    return render_template("add_task.html",title='Edit Subtask', task=subtask,name=name,submit_url=url_for('edit_subtask',subtask_id=subtask.id))

@app.route('/delete/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    try:
        task=Task.query.filter_by(id=task_id,user_id=session["user_id"]).first_or_404()
        db.session.delete(task)
        db.session.commit()
        remaining = Task.query.filter_by(user_id=session["user_id"]).count()
        if request.headers.get('HX-Request'):
            if remaining==0:
                return '<main class="content" id="tasks-container" hx-swap-oob="true"><h2 class="no-tasks-message">No active tasks.</h2></main>', 200
            return f'''<ul class="subtask-tree" id="subtasks-{task_id}" hx-swap-oob="delete"></ul>''',200
    except:
        db.session.rollback()
        if request.headers.get('HX-Request'):
            return "", 400
    return redirect(url_for("dashboard"))

@app.route("/delete_suggestion_task/<int:task_id>/<_id_>",methods=['DELETE'])
@login_required
def delete_suggestion_task(task_id,_id_):
    user = User.query.get(session["user_id"])
    name=user.name
    try:
        task = AISuggestions.query.filter_by(id=task_id, user_id=session["user_id"]).first_or_404()
        db.session.delete(task)
        db.session.commit()
        if request.headers.get('HX-Request'):
            return "",200
    except:
        db.session.rollback()
        if request.headers.get('HX-Request'):
            return "",400
    return render_template("ai_suggestions.html",title="suggestions",tasks=tasks,id=_id_,name=name)


@app.route("/delete_completed_task/<int:task_id>",methods=['DELETE'])
@login_required
def delete_completed_task(task_id):
    try:
        task = CompletedTask.query.filter_by(id=task_id, user_id=session["user_id"]).first_or_404()
        db.session.delete(task)
        db.session.commit()
        remaining=CompletedTask.query.filter_by(user_id=session["user_id"]).count()
        if request.headers.get('HX-Request'):
            if remaining==0:
                return '<main class="content" id="completed-tasks-container" hx-swap-oob="true"><h2>No completed tasks</h2></main>'
            return "",200
    except :
        db.session.rollback()
        if request.headers.get('HX-Request'):
            return "",400
    return redirect(url_for("completed_tasks"))

@app.route("/delete_subtask/<int:subtask_id>",methods=['DELETE'])
@login_required
def delete_subtask(subtask_id):
    try:
        subtask = SubTask.query.filter_by(id=subtask_id, user_id=session["user_id"]).first_or_404()
        db.session.delete(subtask)
        db.session.commit()
        if request.headers.get('HX-Request'):
            return "",200
    except Exception:
        db.session.rollback()
        if request.headers.get('HX-Request'):
            return "",400
        
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

@app.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    try:
        task = Task.query.filter_by(id=task_id,user_id=session["user_id"]).first_or_404()
        completed_task = CompletedTask(title=task.title,user_id=session["user_id"],completed_at=datetime.now(timezone.utc),category=task.category,priority=task.priority)
        db.session.add(completed_task)
        db.session.delete(task)
        user = User.query.filter_by(id=session['user_id']).first_or_404()
        #!!
        time_to_complete=(datetime.now(timezone.utc)-task.created_at.replace(tzinfo=timezone.utc)).total_seconds()/3600
        if user.weekly_completed_tasks == 0:
            user.average_completion_time=float(time_to_complete)
        else:
            current_total_time = user.average_completion_time*user.weekly_completed_tasks
            new_time = current_total_time + time_to_complete
            user.average_completion_time = new_time / (user.weekly_completed_tasks)
        user.weekly_completed_tasks+= 1
        user.total_completed_tasks += 1
        #!!
        if user.categories:
            liste = user.categories.split(',')
            if task.category != None:
                liste.append(task.category)
            user.categories = ",".join(liste)
        else:
            user.categories = task.category
        #!!
        if user.priorities:
            priorities=user.priorities
            high=priorities['high']
            medium=priorities['medium']
            low=priorities['low']
            current_priorities={'high':high,'medium':medium,'low':low}
            current_priorities[task.priority.lower()]+=1
            user.priorities = dict(current_priorities)
        else:
            user.priorities={'high':0,'medium':0,'low':0}
        #!!
        db.session.commit()
        remaining = Task.query.filter_by(user_id=session["user_id"]).count()
        if request.headers.get("HX-Request"):
            if remaining==0:
                return '<main class="content" id="tasks-container" hx-swap-oob="true"><h2 class="no-tasks-message">No active tasks.</h2></main>', 200
            return f'''<ul class="subtask-tree" id="subtasks-{task_id}" hx-swap-oob="delete"></ul>''',200
    except:
        db.session.rollback()
        if request.headers.get("HX-Request"):
            return "",400
    return redirect(url_for("dashboard"))

@app.route('/complete_subtask/<int:subtask_id>',methods=['POST'])
@login_required
def complete_subtask(subtask_id):
    try:
        task=SubTask.query.filter_by(id=subtask_id,user_id=session["user_id"]).first_or_404()
        title = task.title
        completed_task = CompletedTask(title=title,user_id=session["user_id"],completed_at=datetime.now(timezone.utc),category=task.category,priority=task.priority)
        db.session.add(completed_task)
        db.session.delete(task)
        db.session.commit()
        if request.headers.get("HX-Request"):
            return "",200
    except:
            db.session.rollback()
            if request.headers.get("HX-Request"):
                return "",400
    return redirect(url_for("dashboard"))

@app.route('/completed')
@login_required
def completed_tasks():
    user = User.query.get(session["user_id"])
    name=user.name
    try:
        purge_expired_tasks()
        tasks = CompletedTask.query.filter_by(user_id=session["user_id"]).all()
        for i in tasks:
            expiration_time = i.completed_at.replace(tzinfo=timezone.utc) + timedelta(hours=12)
            i.time_left = expiration_time - datetime.now(timezone.utc)
            total_seconds = int(i.time_left.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            i.formatted_time_left = f"{hours}H {minutes}min"
    except:
        flash("Something went wrong", "error")
        db.session.rollback()
    return render_template("completed.html", title="Completed Tasks", tasks=tasks, status="completed_tasks",name=name)


@app.route('/break-down/<task_id>',methods=['GET','POST'])
@login_required
def break_down(task_id):
    user = User.query.get(session["user_id"])
    name=user.name
    try:
        AISuggestions.query.filter_by(user_id=session['user_id']).delete()
        task=Task.query.filter_by(user_id=session['user_id'],id=task_id).first_or_404()
        subtasks=ai_models.break_down_task(task.title)
        breaked_tasks=[]
        for subtask in subtasks:
            new_task = AISuggestions(title=subtask['subtask'],priority=subtask['priority'],due_date=None,user_id=session["user_id"])
            db.session.add(new_task)
            breaked_tasks.append(new_task)
            db.session.commit()
    except:
        flash('Something went wrong','error')
        db.session.rollback()
    return render_template("ai_suggestions.html",title="suggestions",tasks=breaked_tasks,id=task_id,name=name)

@app.route('/confirm-break-down/<task_id>')
@login_required
def confirm_break_down(task_id):
    try:
        suggestions = AISuggestions.query.filter_by(user_id=session["user_id"])
        parent_task=Task.query.filter_by(user_id=session['user_id'],id=task_id).first_or_404()
        for i in suggestions:
            new_subtask = SubTask(parent_task=parent_task,title=i.title,priority=i.priority,category=i.category,due_date=i.due_date,user_id=session["user_id"])
            db.session.add(new_subtask)
            db.session.delete(i)
        parent_task.evaluate=False
        suggestions.delete()
        db.session.commit()
        flash('SubTasks added successfully!','success')
    except:
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

@app.route('/statics')
@login_required
def statics():
    user=User.query.filter_by(id=session['user_id']).first_or_404()
    statics=insights(user)
    charts=[]
    category_labels=[]
    category_values=[]
    category_results = db.session.query(CompletedTask.category, db.func.count(CompletedTask.id)).group_by(CompletedTask.category).all()
    if category_results:
        for r in category_results:
            if r[0] :
                category_labels.append(r[0])
                category_values.append(r[1])
    else:
        category_labels=['NoData']
    charts.append({'id':'categorychart','title':'Categories Distribution','labels':category_labels,'values':category_values})
    priority_labels=['High','Medium','Low']
    priority_values=[value for value in statics['Count completed tasks by priority'].values()]
    charts.append({'id':'prioritychart','title':'Priority Distribution','labels':priority_labels,'values':priority_values})
    print(f"================={statics},========={charts}")
    return render_template('statics.html', charts=charts, statics=statics, status='statics')
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
        db.drop_all()
        db.create_all()
    else:
        db.create_all()
if __name__ == "__main__":
    app.run(debug=True)
    print("================ Application Stoped ================")