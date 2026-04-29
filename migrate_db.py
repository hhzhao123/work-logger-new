#!/usr/bin/env python3
"""
数据库迁移脚本：修复 task 表结构
在 PythonAnywhere 上运行此脚本：
    python migrate_db.py
"""
from app import app, db
from sqlalchemy import inspect, text

with app.app_context():
    inspector = inspect(db.engine)
    
    # 检查 task 表是否存在
    tables = inspector.get_table_names()
    
    if 'task' not in tables:
        print('task 表不存在，无需迁移')
        db.create_all()
        print('数据库已创建')
        exit(0)
    
    # 获取当前字段
    columns = [col['name'] for col in inspector.get_columns('task')]
    print('当前字段:', columns)
    
    # 如果还有旧的 date 字段
    if 'date' in columns:
        print('检测到旧的 date 字段，开始迁移...')
        
        # SQLite 不支持 DROP COLUMN，需要重建表
        # 1. 创建新表
        db.engine.execute(text('''
            CREATE TABLE task_new (
                id INTEGER NOT NULL PRIMARY KEY,
                content TEXT NOT NULL,
                done BOOLEAN DEFAULT 0,
                created_at DATETIME,
                completed_at DATETIME
            )
        '''))
        
        # 2. 复制数据（如果旧表有数据）
        try:
            db.engine.execute(text('''
                INSERT INTO task_new (id, content, done, created_at, completed_at)
                SELECT id, content, done, 
                       CASE WHEN date IS NOT NULL THEN date ELSE NULL END as created_at, 
                       completed_at
                FROM task
            '''))
            print('数据已迁移')
        except Exception as e:
            print(f'数据迁移警告: {e}')
        
        # 3. 删除旧表
        db.engine.execute(text('DROP TABLE task'))
        
        # 4. 重命名新表
        db.engine.execute(text('ALTER TABLE task_new RENAME TO task'))
        
        print('迁移完成！')
    else:
        print('数据库结构正常，无需迁移')
    
    # 重新检查
    columns = [col['name'] for col in inspector.get_columns('task')]
    print('迁移后字段:', columns)
