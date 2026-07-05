from database import db
from datetime import date, timedelta
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100),unique=True,nullable=False)
    name = db.Column(db.String(100),unique=False,nullable=False)
    password = db.Column(db.String(200),nullable=False)
    tasks = db.relationship("Task", backref="user", lazy=True)
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    title = db.Column(db.String(300),nullable=False)
    priority = db.Column(db.String(10),nullable=False)
    category = db.Column(db.String(50), default=None)
    due_date = db.Column(db.Date,nullable=True)
    @property
    def friendly_date(self):
        today = date.today()
        if self.due_date == today:
            return "Today"
        elif self.due_date == today + timedelta(days=1):
            return "Tomorrow"
        elif self.due_date == today - timedelta(days=1):
            return "Yesterday"
        return self.due_date.strftime("%d-%m-%Y")
    evaluate = db.Column(db.Boolean, default=False, nullable=False)
    subtasks = db.relationship('SubTask', backref='parent_task', lazy=True, cascade="all, delete-orphan")
class SubTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    parent_id=db.Column(db.Integer,db.ForeignKey('task.id'),nullable=False)
    title = db.Column(db.String(300),nullable=False)
    priority = db.Column(db.String(10),nullable=False)
    category = db.Column(db.String(50), default=None)
    due_date = db.Column(db.Date,nullable=True)
    @property
    def friendly_date(self):
        today = date.today()
        if self.due_date == today:
            return "Today"
        elif self.due_date == today + timedelta(days=1):
            return "Tomorrow"
        elif self.due_date == today - timedelta(days=1):
            return "Yesterday"
        return self.due_date.strftime("%d-%m-%Y")
class AISuggestions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300),nullable=False)
    priority = db.Column(db.String(10),nullable=False)
    category = db.Column(db.String(50), default=None)
    due_date = db.Column(db.Date,nullable=True)
    user_id = db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
class CompletedTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300),nullable=False)
    due_date = db.Column(db.Date,nullable=True)
    user_id = db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)