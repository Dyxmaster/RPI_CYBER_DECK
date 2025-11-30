from flask import Blueprint, jsonify
from modules import system_ctl
from flask_login import login_required
bp = Blueprint('api_system', __name__)

@bp.route('/api/system/<action>', methods=['POST'])
@login_required
def system_action(action):
    success = False
    msg = ""
    
    if action == 'shutdown':
        success, msg = system_ctl.shutdown()
    elif action == 'reboot':
        success, msg = system_ctl.reboot()
    else:
        return jsonify({"status": "error", "msg": "未知指令"}), 400
    
    if success:
        return jsonify({"status": "ok", "msg": f"系统正在执行: {action}..."})
    else:
        return jsonify({"status": "error", "msg": f"执行失败: {msg}"}), 500