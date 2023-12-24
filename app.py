from flask import Flask, render_template, render_template_string, request, redirect, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban.db'
db = SQLAlchemy(app)
# app.static_folder = 'projects'


class NewProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)
    project_number = db.Column(db.String(50), unique=True, nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    tasks = db.relationship('Task', backref='project', lazy=True)

# class Task(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(200), nullable=False)
#     status = db.Column(db.String(20), nullable=False)
#     date_created = db.Column(db.DateTime, default=datetime.utcnow)
#     project_id = db.Column(db.Integer, db.ForeignKey('new_project.id'), nullable=False)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    project_number = db.Column(db.String(50), db.ForeignKey('new_project.project_number'), nullable=False)
    # project_id = db.Column(db.Integer, db.ForeignKey('new_project.id'), nullable=False)  # Add this line

    # ... rest of the model definition



class ProjectTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey(
        'new_project.id'), nullable=False)


class Totals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_projects = db.Column(db.Integer, default=0)
    total_todos = db.Column(db.Integer, default=0)
    total_inprogress = db.Column(db.Integer, default=0)
    total_completed = db.Column(db.Integer, default=0)


class ProgressInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('new_project.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    total_projects = db.Column(db.Integer)
    total_todos = db.Column(db.Integer)
    total_inprogress = db.Column(db.Integer)
    total_completed = db.Column(db.Integer)


def update_progress():
    current_date = datetime.utcnow()

    # Calculate the target date for the last 30 days
    target_date = current_date - timedelta(days=30)

    # Count tasks for the last 30 days
    total_projects = NewProject.query.filter(NewProject.id > 0).count()
    total_todos = Task.query.filter(
        Task.status == 'To Do', Task.id > 0, Task.date_created >= target_date).count()
    total_inprogress = Task.query.filter(
        Task.status == 'In Progress', Task.id > 0, Task.date_created >= target_date).count()
    total_completed = Task.query.filter(
        Task.status == 'Done', Task.id > 0, Task.date_created >= target_date).count()

    # Calculate progress percentage
    target_project = 5  # Adjust the target value as needed, e.g., 5 projects in a month
    target = 5  # You can adjust the target value as needed
    progress_projects = (total_projects / target_project) * 100
    progress_todos = (total_todos / target) * 100
    progress_inprogress = (total_inprogress / target) * 100
    progress_completed = (total_completed / target) * 100

    print("Total Projects:", total_projects)
    print("Total To-Do:", total_todos)
    print("Total In-Progress:", total_inprogress)
    print("Total Completed:", total_completed)

    # Store progress information in the database
    progress_info = ProgressInfo(
        timestamp=current_date,
        total_projects=progress_projects,
        total_todos=progress_todos,
        total_inprogress=progress_inprogress,
        total_completed=progress_completed
    )

    db.session.add(progress_info)
    db.session.commit()


def update_totals():
    total_projects = NewProject.query.count()
    total_todos = Task.query.filter_by(status='To Do').count()
    total_inprogress = Task.query.filter_by(status='In Progress').count()
    total_completed = Task.query.filter_by(status='Done').count()

    totals = Totals.query.first()
    if not totals:
        totals = Totals()
        db.session.add(totals)

    totals.total_projects = total_projects
    totals.total_todos = total_todos
    totals.total_inprogress = total_inprogress
    totals.total_completed = total_completed

    db.session.commit()







def create_kanban_template(project_number):
    # Fetch tasks related to the project_number
    tasks = Task.query.filter_by(project_number=project_number).all()

    # Specify the correct path to your template file within the "templates" folder
    template_file_path = os.path.join(app.root_path, 'templates', 'kanban_template.html')

    with open(template_file_path, 'r') as file:
        template_content = file.read()

    # Manually replace placeholders in the template content
    template_content = template_content.replace('{{ project_number }}', str(project_number))
    
    # Render the Kanban template with the tasks
    rendered_template = render_template_string(template_content, tasks=tasks)

    # Create a folder for each project if it doesn't exist
    project_folder_path = os.path.join(app.root_path, 'projects', str(project_number))
    os.makedirs(project_folder_path, exist_ok=True)
    print("Started creating project...")

    # Create a unique HTML file for the Kanban template and save it in the project folder
    file_path = os.path.join(project_folder_path, f'{project_number}.html')
    with open(file_path, 'w') as file:
        file.write(rendered_template)
    print("Done creating project...")

    return file_path

@app.route('/', methods=['GET', 'POST'])
def index():
    # tasks = Task.query.all()
    totals = Totals.query.first()
    progress_info = ProgressInfo.query.order_by(
        ProgressInfo.timestamp.desc()).first()
    return render_template('index.html', totals=totals, progress_info=progress_info)


# @app.route('/add', methods=['POST'])
# def add():
#     title = request.form.get('title')
#     project_id = request.form.get('project_id')

#     # Assuming you have a date_created field in your Task model
#     date_created = datetime.utcnow()

#     # Check if project_id is None
#     if project_id is None:
#         # Handle the case where project_id is not provided (you may redirect or show an error message)
#         return redirect(url_for('index'))

#     new_task = Task(title=title, status='To Do',
#                     date_created=date_created, project_id=project_id)
#     db.session.add(new_task)
#     db.session.commit()

#     # After adding the new task, update the progress and totals
#     update_progress()
#     update_totals()

#     return redirect(url_for('index'))


@app.route('/add', methods=['POST'])
def add():
    title = request.form.get('title')
    project_number = request.form.get('project_number')  # Use project_number instead of project_id

    # Assuming you have a date_created field in your Task model
    date_created = datetime.utcnow()

    # Check if project_number is None
    if project_number is None:
        # Handle the case where project_number is not provided (you may redirect or show an error message)
        return redirect(url_for('index'))

    # Create a new task with the provided project_number
    new_task = Task(title=title, status='To Do', date_created=date_created, project_number=project_number)
    db.session.add(new_task)
    db.session.commit()

    # After adding the new task, update the progress and totals
    update_progress()
    update_totals()

    # Redirect the user to the newly created Kanban page
    return redirect(url_for('kanban', project_number=project_number))



@app.route('/update/<int:id>/<status>', methods=['GET'])
def update(id, status):
    task = Task.query.get(id)
    task.status = status
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/delete/<int:id>')
def delete(id):
    task = Task.query.get(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    return render_template('signin.html')

# @app.route('/create_new_project', methods=['GET','POST'])
# def create_new_project():
#     return render_template('new_project.html')


@app.route('/new_project', methods=['GET', 'POST'])
def new_project():
    if request.method == 'POST':
        project_name = request.form['project_name']
        project_number = request.form['project_number']
        author_name = request.form['author_name']

        new_project = NewProject(
            project_name=project_name,
            project_number=project_number,
            author_name=author_name
        )

        db.session.add(new_project)
        db.session.commit()

        # Update totals
        update_totals()
        update_progress()

        return redirect(url_for('index'))

    return render_template('new_project.html')


@app.route('/create_kanban/<project_number>', methods=['GET', 'POST'])
def create_kanban(project_number):
    # Get the file path of the generated Kanban template
    file_path = create_kanban_template(project_number)

    # Serve the dynamically created HTML file
    return send_from_directory('projects', f'{project_number}/{project_number}.html')


@app.route('/kanban/<project_number>',methods=['GET', 'POST'])
def kanban(project_number):
    # Fetch tasks related to the project_number
    tasks = Task.query.filter_by(project_number=project_number).all()

    return render_template('kanban_template.html', project_number=project_number, tasks=tasks)

@app.route('/all_project', methods=['GET', 'POST'])
def all_project():
    projects = NewProject.query.all()

    return render_template('all_projects.html', projects=projects)

@app.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    # Fetch the project by ID
    project = NewProject.query.get(project_id)

    if request.method == 'POST':
        # Fetch related tasks and progress info
        tasks_to_delete = Task.query.filter_by(project_number=project.project_number).all()
        progress_info_to_delete = ProgressInfo.query.filter_by(
            project_id=project.id).all()

        # Delete the project and related tasks and progress info
        db.session.delete(project)
        for task in tasks_to_delete:
            db.session.delete(task)
        for progress_info in progress_info_to_delete:
            db.session.delete(progress_info)

        db.session.commit()

        # Fetch the updated list of projects
        projects = NewProject.query.all()

        return render_template('all_projects.html', projects=projects)

    # If not a POST request, render the template with the existing projects
    return render_template('all_projects.html', projects=[project])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        update_totals()
    app.run(debug=True)
