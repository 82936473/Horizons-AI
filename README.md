# Smart Planner
![Python](https://img.shields.io/badge/Python-3.13-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-black)
![SQLite](https://img.shields.io/badge/SQLite-Database-blue)
![License](https://img.shields.io/badge/Status-Active-brightgreen)  
 An intelligent, responsive task management platform built with Flask.  
 note: This project is for Horizons.

--------------

## <span style="color:#F1E05A">Why I built it</span>
The idea for this project came to me several months ago when I discovered GitHub and the open-source community. At this time, I was learning Python in my free time and wanted to build a real project instead of just following tutorials.

The first version was a simple terminal application where users managed their tasks by choosing options with indexes like (y/n). I was proud of it because it was my first complete project, but I knew I could make it better.

For the second version, I redesigned the interface so users interacted with the application through terminal commands, similar to Git. Although it was an improvement, I still wanted to transform it into a real web application. Unfortunately, I didn't have enough motivation at that moment, and I was busy with exams.

Later, while scrolling through social media, I discovered Hack Club and learned about Horizons. After a deep search and after trust the community. It gave me the motivation to finally build the web version of my project.
During development, I migrated the application from CSV file storage to a SQLite database using SQLAlchemy to improve scalability and data management.

[You can see the project versions in the project tags](https://github.com/82936473/Horizons-AI/tags)

--------------

## <span style="color:#F1E05A">Features</span>

*   **🔐 Secure Authentication:** sign-up, log in, log out, and protected personal tasks and projects dashboards.
*   **✅ Task Management:** Full CRUD operations easily add, edit, complete, and delete tasks.
*   **🚩 Smart Organization:** Assign task priorities, categories, and set due dates.
*   **🧠 Smart Categorization:** Automaticlly detects task categories.
*   **📂 Project Management:** Smart project management, (add, edit, delete), orginazed with milestones.
*   **⚡ Quick Add:** Quick add tasks easily by describing it, and generate full projects using AI.
*   **📅 Weekly Summary:** Recieve an email every week contain the sammary of your progress and actions.
*   **📈 Statistics:** Track your productivity with a clear visual analytics.
*   **📱 Responsive Interface:** A clean, modern user interface optimized for desktop and mobile screens.

--------------

## <span style="color:#F1E05A">How it works</span>
In the first time trying the application, you should sign up by dropping your email, creating a password, and choose a name.  
You'll have a personal account protected by password hashing.
After logging in, you can:
### <span style="color:#7EE787">In Tasks Dashboard</span>
* Create, Edit, Complete, Delete tasks, and delete all tasks.
* Assign a priority (High, Medium, or Low).
* Assign a category. Auto detect if you leave it empty.
* Set an optional due date.
* Sort tasks by priority, due date, or alphabetical order.
* Quick add tasks easily using AI with auto priority, category, due date, complexity detect.
* The Quick add function will return subtasks in case of complex given task.
### <span style="color:#7EE787">In Projects Dashboard</span>
* Create, Edit, Delete projects.
* Set a title, a goal, and assign a decription, a color and a target date for the project.
* Create tasks inside Milestones for better categorization.
* Complete tasks, milestones, and projects.
* Generate the full project intelligently and easily using AI.
### <span style="color:#7EE787">In Statistics Page</span>
You can track:
* total completed tasks, and weekly completed tasks.
* Average completion time.
* Top category.
* Top priority.
* Total completed projects.
* Total active projects.
* Category and priority distribution through charts.


All data is stored in a SQLite database using SQLAlchemy and secure Flask session management, ensuring that every user's tasks remain private.

--------------


## <span style="color:#F1E05A">Technologies</span>
* Flask
* SQLite
* SQLAlchemy
* HTML5, CSS3, JavaScript

--------------

## <span style="color:#F1E05A">Installation & Setup</span>
Clone the repository:
```bash
git clone https://github.com/82936473/Horizons-AI.git
```
Install the requirements:
```bash
pip install -r requirements.txt
```
Create .env file and fill the variables
```bash
API_KEY = ... "the application use Groq, you can change that in the main.py file"
RESET_DB = False "Put True if you want to clean the database everytime tou restart the application"
SECRET_KEY = "long secret key for flask session security"
address_email = 'your private address-email'
password_email = 'Mail password'
```
Run the Application:
```bash
python main.py
```
--------------

## <span style="color:#F1E05A">Future improvements</span>
* Multiple languages.
* Dark mode.
* ADD Date and time for tasks instead of Date only.

--------------
## <span style="color:#F1E05A">Live Demo</span>
[Check out the acual live website.](https://smartplanner.ayman.hackclub.app/)

--------------
## <span style="color:#F1E05A">What I used AI for</span>
The majority of the project was full human creating, from searching the idea to applying it.  
But AI Help was present in:
- learn how to use flask, css, and javascript in the first website version building steps. (I didn't use youtube tutorials a lot)
- resolving bugs.
- getting project ideas.
- improving design to be more professional (emojis, svg, colors).
- analyse API outputs and suggest solutions.

--------------

## <span style="color:#F1E05A">Project Improuvement
* ### Home:
|Before|After|
|---------|---------|
|![](images/image1.png)|![](images/home.png)|
* ### Sign up:
|Before|After|
|-----|-----|
|![](images/image3.png)|![Sign up](images/signup.png)|
* ### Tasks Dashboard
|Before|After|
|--------|---------|
|![](images/image5.png)|![](images/dashboard.png)|
* ### Added Features:
Projects:
![Projects](images/projects.png)
Statistics:
![Statistics](images/statistics.png)
--------------


## What I learned During This Project
During this project, I learned:

- Flask routing.
- HTML & CSS.
- SQLAlchemy and SQLite.
- User authentication.
- Password hashing.
- Responsive web design.
- Git and GitHub workflow.
- HTMX and background communication.