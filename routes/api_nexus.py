from flask import Blueprint, jsonify, request
from modules.nexus_core import nexus_brain
from flask_login import login_required

# 定义蓝图名称为 bp_nexus，方便 app.py 引用
bp_nexus = Blueprint('api_nexus', __name__)

@bp_nexus.route('/api/nexus/init', methods=['GET'])
@login_required
def init_nexus():
    """初始化页面数据"""
    data = nexus_brain.generate_briefing()
    return jsonify({"status": "ok", "data": data})

@bp_nexus.route('/api/nexus/chat', methods=['POST'])
@login_required
def chat():
    """对话接口"""
    req = request.get_json()
    msg = req.get('msg', '')
    if not msg:
        return jsonify({"reply": "输入无效"})
    
    reply = nexus_brain.chat_router(msg)
    return jsonify({"status": "ok", "reply": reply})

@bp_nexus.route('/api/nexus/task/add', methods=['POST'])
@login_required
def add_task():
    """添加任务"""
    req = request.get_json()
    content = req.get('content')
    if content:
        nexus_brain.add_task(content)
    # 返回最新任务列表
    return jsonify({"status": "ok", "tasks": nexus_brain.get_tasks()})

@bp_nexus.route('/api/nexus/task/complete', methods=['POST'])
@login_required
def complete_task():
    """完成任务"""
    req = request.get_json()
    task_id = req.get('id')
    if task_id:
        nexus_brain.complete_task(task_id)
    return jsonify({"status": "ok", "tasks": nexus_brain.get_tasks()})