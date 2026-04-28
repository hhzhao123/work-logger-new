from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///work_logs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class WorkLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    project = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    duration = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/logs', methods=['GET'])
def get_logs():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = WorkLog.query
    if start_date:
        query = query.filter(WorkLog.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(WorkLog.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    logs = query.order_by(WorkLog.date.desc()).all()
    return jsonify([{
        'id': log.id,
        'date': log.date.strftime('%Y-%m-%d'),
        'project': log.project,
        'content': log.content,
        'duration': log.duration
    } for log in logs])

@app.route('/api/logs', methods=['POST'])
def add_log():
    data = request.json
    log = WorkLog(
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        project=data['project'],
        content=data['content'],
        duration=data.get('duration', 1.0)
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({'id': log.id})

@app.route('/api/logs/<int:log_id>', methods=['DELETE'])
def delete_log(log_id):
    log = WorkLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    return '', 204

@app.route('/api/report', methods=['GET'])
def generate_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    report_type = request.args.get('type', 'week')
    
    if not start_date:
        if report_type == 'week':
            start_date = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d')
        else:
            start_date = (datetime.now().replace(day=1)).strftime('%Y-%m-%d')
    
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    logs = WorkLog.query.filter(
        WorkLog.date >= datetime.strptime(start_date, '%Y-%m-%d').date(),
        WorkLog.date <= datetime.strptime(end_date, '%Y-%m-%d').date()
    ).all()
    
    total_hours = sum(log.duration for log in logs)
    projects = {}
    for log in logs:
        projects[log.project] = projects.get(log.project, 0) + log.duration
    
    report = f"# {'周报' if report_type == 'week' else '月报'}\n"
    report += f"时间范围: {start_date} 至 {end_date}\n\n"
    report += f"## 总体统计\n"
    report += f"- 总工时: {total_hours} 小时\n"
    report += f"- 记录条数: {len(logs)} 条\n\n"
    report += f"## 项目分布\n"
    for proj, hours in sorted(projects.items(), key=lambda x: x[1], reverse=True):
        report += f"- {proj}: {hours} 小时\n"
    report += f"\n## 详细记录\n"
    for log in sorted(logs, key=lambda x: x.date):
        report += f"\n### {log.date.strftime('%Y-%m-%d')} - {log.project}\n"
        report += f"耗时: {log.duration}小时\n"
        report += f"内容: {log.content}\n"
    
    return jsonify({'report': report})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
else:
    import os
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///work_logs.db')
