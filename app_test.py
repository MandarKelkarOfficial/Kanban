from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban.db'
db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)

@app.route('/')
def index():
    tasks = Task.query.all()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add():
    title = request.form.get('title')
    new_task = Task(title=title, status='To Do')
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))

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



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
