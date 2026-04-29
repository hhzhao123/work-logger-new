from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///work_logs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'
db = SQLAlchemy(app)

# 用户表
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# 任务表
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)  # 计划日期
    content = db.Column(db.Text, nullable=False)
    done = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)  # 完成时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
    
    # 检查并添加缺失的列
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    if 'task' in tables:
        columns = [col['name'] for col in inspector.get_columns('task')]
        if 'completed_at' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE task ADD COLUMN completed_at DATETIME'))
                conn.commit()
                print('已添加 completed_at 列到 task 表')

# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        return render_template('login.html', error='用户名或密码错误')
    return render_template('login.html')

# 注册页面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='用户名已存在')
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# 退出登录
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 首页
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

# 获取任务列表
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    date = request.args.get('date')
    done = request.args.get('done')  # 新增：完成状态筛选
    
    query = Task.query
    
    if date:
        query = query.filter_by(date=datetime.strptime(date, '%Y-%m-%d').date())
    
    if done is not None:
        done_bool = done.lower() == 'true'
        query = query.filter_by(done=done_bool)
    
    tasks = query.all()
    return jsonify([{
        'id': task.id,
        'date': task.date.strftime('%Y-%m-%d'),
        'content': task.content,
        'done': task.done,
        'created_at': task.created_at.strftime('%Y-%m-%d %H:%M') if task.created_at else '',
        'completed_at': task.completed_at.strftime('%Y-%m-%d %H:%M') if task.completed_at else ''
    } for task in tasks])

# 添加任务
@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.json
    task = Task(
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        content=data['content']
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({'id': task.id})

# 更新任务状态
@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.json
    if 'done' in data:
        task.done = data['done']
        if data['done']:
            task.completed_at = datetime.now()  # 使用本地时间
        else:
            task.completed_at = None  # 取消完成，清空时间
    db.session.commit()
    return '', 204

# 删除任务
@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return '', 204

# 生成报告
@app.route('/api/report', methods=['GET'])
def generate_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 如果没传时间范围，使用默认值
    if not start_date:
        start_date = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # 按完成时间筛选，只统计已完成的任务
    tasks = Task.query.filter(
        Task.done == True,
        Task.completed_at >= datetime.strptime(start_date, '%Y-%m-%d').date(),
        Task.completed_at < datetime.strptime(end_date, '%Y-%m-%d').date() + timedelta(days=1)
    ).all()
    
    total = len(tasks)
    
    report = f"# 工作报告\n"
    report += f"统计时间: {start_date} 至 {end_date}（按完成时间统计）\n\n"
    report += f"## 总体统计\n"
    report += f"- 已完成任务: {total} 项\n\n"
    report += f"## 已完成任务明细\n"
    for task in sorted(tasks, key=lambda x: x.completed_at):
        report += f"- {task.content}\n"  # 报告里不显示时间
    
    return jsonify({'report': report})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
