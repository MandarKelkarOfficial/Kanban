from flask import Flask, jsonify, render_template, render_template_string, request, redirect, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import JSON 
from werkzeug.utils import secure_filename
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Set up credentials
# scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('keyKanban.json')
client = gspread.authorize(creds)

# creds = ServiceAccountCredentials.from_json_keyfile_name('path/to/your/credentials.json', scope)
# client = gspread.authorize(creds)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban.db'
db = SQLAlchemy(app)





class NewProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)
    project_number = db.Column(db.String(50), unique=True, nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    tasks = db.relationship('Task', backref='project', lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
        # New column for storing multiple image URLs
    images = db.Column(JSON, default=[])
    status = db.Column(db.String(20), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    project_number = db.Column(db.String(50), db.ForeignKey(
        'new_project.project_number'), nullable=False)


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



# # Function to create a new sheet for each project

# def create_project_sheet(project_number):
#     # Open the KANBAN workbook
#     gc = gspread.service_account(filename='keyKanban.json')
#     workbook = gc.open("KANBAN")

#     # Use the project number as the title of the new sheet
#     new_sheet = workbook.add_worksheet(title=project_number, rows="100", cols="20")

#     # Set up headers in the new sheet
#     new_sheet.update('A1', [['Task ID', 'Title', 'Status', 'Date Created', 'Image URLs']])
#     new_sheet.format('A1:F1', {'textFormat': {'bold': True}})

#     # Fetch data from the Task table for the specific project number
#     tasks = Task.query.filter_by(project_number=project_number).all()

#     # Prepare the data to be written to the sheet
#     data = [[task.id, task.title, task.status, str(task.date_created)] for task in tasks]

#     # Write the data to the sheet, starting from row 2 (A2)
#     new_sheet.update('A3', data)

def create_project_sheet(project_number):
    # Open the KANBAN workbook
    gc = gspread.service_account(filename='keyKanban.json')
    workbook = gc.open("KANBAN")

    # Use the project number as the title of the new sheet
    new_sheet = workbook.add_worksheet(title=project_number, rows="100", cols="10")

    # Set up headers in the new sheet
    header_values = [['Task ID', 'Title', 'Status', 'Date Created', 'Image URLs']]
    new_sheet.update('B1', header_values)

    # Format headers with 'light cornflower blue 1' color
    new_sheet.format('B1:F1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 1}})

    # Fetch data from the Task table for the specific project number
    tasks = Task.query.filter_by(project_number=project_number).all()

    # Prepare the data to be written to the sheet
    data = [[task.id, task.title, task.status, str(task.date_created)] for task in tasks]

    # Write the data to the sheet, starting from row 2 (A2)
    new_sheet.update('B3', data)

    # Define color codes for different statuses
    color_codes = {'Done': {'red': 0, 'green': 1, 'blue': 0},
                   'To Do': {'red': 1, 'green': 0.6, 'blue': 0},
                   'In Progress': {'red': 1, 'green': 1, 'blue': 0}}

    # Apply colors to rows based on status
    for i, task in enumerate(tasks, start=3):
        status_color = color_codes.get(task.status, {'red': 1, 'green': 1, 'blue': 1})  # Default to white
        color_range = f'B{i}:F{i}'
        new_sheet.format(color_range, {'backgroundColor': status_color})




@app.route('/', methods=['GET', 'POST'])
def index():
    # tasks = Task.query.all()
    totals = Totals.query.first()
    progress_info = ProgressInfo.query.order_by(
        ProgressInfo.timestamp.desc()).first()
    return render_template('index.html', totals=totals, progress_info=progress_info)

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    return render_template('signin.html')


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

        # Save the new project
        db.session.add(new_project)
        db.session.commit()

        # Create a table for the project tasks
        # create_project_table(project_number)

        # Update totals and progress
        update_totals()
        update_progress()

        return redirect(url_for('all_project'))

    return render_template('new_project.html')



# @app.route('/add', methods=['POST'])
# def add():
#     title = request.form.get('title')
#     # Use project_number instead of project_id
#     project_number = request.form.get('project_number')

#     # Assuming you have a date_created field in your Task model
#     date_created = datetime.utcnow()

#     # Check if project_number is None
#     if project_number is None:
#         # Handle the case where project_number is not provided (you may redirect or show an error message)
#         return redirect(url_for('index'))

#     # Create a new task with the provided project_number
#     new_task = Task(title=title, status='To Do',
#                     date_created=date_created, project_number=project_number)
#     db.session.add(new_task)
#     db.session.commit()

#     # After adding the new task, update the progress and totals
#     update_progress()
#     update_totals()

#     # Redirect the user to the newly created Kanban page
#     return redirect(url_for('kanban', project_number=project_number))


@app.route('/add', methods=['POST'])
def add():
    title = request.form.get('title')
    project_number = request.form.get('project_number')
    
    # Get a list of image files from the form
    # images = request.files.getlist('images')

    # # Validate and save the attached images
    # uploaded_images = []
    # for image in images:
    #     if image and allowed_file(image.filename):
    #         filename = secure_filename(image.filename)
    #         image_path = os.path.join('uploads', filename)
    #         image.save(image_path)
    #         uploaded_images.append(image_path)

    date_created = datetime.utcnow()

    if project_number is None:
        return redirect(url_for('index'))

    new_task = Task(title=title, status='To Do', date_created=date_created, project_number=project_number)
    db.session.add(new_task)
    db.session.commit()

    update_progress()
    update_totals()

    return redirect(url_for('kanban', project_number=project_number))

@app.route('/update/<int:task_id>/<status>', methods=['POST'])
def update(task_id, status):
    # Update the task status in your database here
    title = request.form.get('title')

    # Assuming you have a date_created field in your Task model
    date_created = datetime.utcnow()

    # Assuming you have a Task model
    task = Task.query.get(task_id)

    # Check if the task exists
    if task:
        task.status = status
        task.date_created = date_created
        db.session.commit()

        # After updating the task, update the progress and totals
        update_progress()
        update_totals()

    return redirect(url_for('kanban', project_number=task.project_number))


@app.route('/delete/<int:id>')
def delete(id):
    task = Task.query.get(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('kanban'))


@app.route('/kanban/<project_number>', methods=['GET', 'POST'])
def kanban(project_number):
    # Fetch tasks related to the project_number
    tasks = Task.query.filter_by(project_number=project_number).all()
    return render_template('test_kanban.html', tasks=tasks, project_number=project_number)


@app.route('/all_project', methods=['GET', 'POST'])
def all_project():
    projects = NewProject.query.all()
    

    return render_template('all_projects.html', projects=projects)


# Modify the delete_project route in your Flask app
@app.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    # Fetch the project by ID
    project = NewProject.query.get(project_id)

    if request.method == 'POST':
        # Fetch related tasks and progress info
        tasks_to_delete = Task.query.filter_by(
            project_number=project.project_number).all()
        progress_info_to_delete = ProgressInfo.query.filter_by(
            project_id=project.id).all()

        # Delete the project and related tasks and progress info
        db.session.delete(project)
        for task in tasks_to_delete:
            db.session.delete(task)
        for progress_info in progress_info_to_delete:
            db.session.delete(progress_info)

        # Drop the project task table
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        table_name = f'project_task_{project.project_number}'

        # Use text construct to create a SQL expression
        drop_table_statement = text(f"DROP TABLE IF EXISTS {table_name}")

        # Use connect method to get a connection, then execute the statement
        with engine.connect() as connection:
            connection.execute(drop_table_statement)

        db.session.commit()

        # Fetch the updated list of projects
        projects = NewProject.query.all()

        return render_template('all_projects.html', projects=projects)

    # If not a POST request, render the template with the existing projects
    return render_template('all_projects.html', projects=[project])


@app.route('/upload_image/<int:task_id>', methods=['POST'])
def upload_image(task_id):
    try:
        task = Task.query.get(task_id)

        if task:
            image = request.files.get('image')

            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image_path = os.path.join('uploads', filename)  # Assuming 'uploads' is a folder in your 'static' directory
                image.save(os.path.join('static', image_path))

                # Update the task's images field with the new image URL
                task.images.append(image_path)
                db.session.commit()

                return jsonify({'success': True, 'message': 'Image uploaded successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

    return jsonify({'success': False, 'error': 'Invalid request'})

# Add the extract route
@app.route('/extract/<int:project_id>', methods=['GET', 'POST'])
def extract(project_id):
    if request.method == 'POST':
        project_number = request.form.get('project_number')

        # Call the function to create a new project sheet
        create_project_sheet(project_number)

        return redirect(url_for('all_project'))

    return redirect(url_for('all_project'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        update_totals()
    app.run(debug=True, host='0.0.0.0', port=8080)
    # serve(create_app())
