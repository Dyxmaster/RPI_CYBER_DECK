from flask import Blueprint, jsonify, request, render_template
from modules.device_ctl import device_mgr
from flask_login import login_required
bp_devices = Blueprint('devices', __name__)

@bp_devices.route('/devices')
@login_required
def index():
    return render_template('devices.html', devices=device_mgr.load_devices(), active_page='devices')

# 1. 轻量轮询：只返回在线状态和延迟
@bp_devices.route('/api/devices/ping_status')
@login_required
def ping_status():
    devices = device_mgr.load_devices()
    results = []
    for d in devices:
        status = device_mgr.get_ping_status(d['ip'])
        status['id'] = d['id']
        results.append(status)
    return jsonify(results)

# 2. 触发 SSH 同步硬件信息
@bp_devices.route('/api/devices/sync_info', methods=['POST'])
@login_required
def sync_info():
    success, msg = device_mgr.fetch_hardware_info(request.json['id'])
    # 如果成功，返回最新的设备数据以便前端更新显示
    new_data = {}
    if success:
        devices = device_mgr.load_devices()
        new_data = next((d for d in devices if str(d['id']) == str(request.json['id'])), {})
    return jsonify({"success": success, "message": msg, "data": new_data})

@bp_devices.route('/api/devices/power', methods=['POST'])
@login_required
def power():
    data = request.json
    success, msg = device_mgr.power_control(data['id'], data['action'])
    return jsonify({"success": success, "message": msg})

@bp_devices.route('/api/devices/edit', methods=['POST'])
@login_required
def edit():
    d = request.json
    # ✨ 这里增加了 d.get('mac') 的接收
    success = device_mgr.edit_device(
        d['id'], 
        d['name'], 
        d['ip'], 
        d.get('ssh_user'), 
        d.get('ssh_pass'), 
        d.get('mac') 
    )
    return jsonify({"success": success})

@bp_devices.route('/api/devices/add', methods=['POST'])
@login_required
def add():
    device_mgr.add_device(request.json['name'], request.json['ip'])
    return jsonify({"success": True})

@bp_devices.route('/api/devices/delete', methods=['POST'])
@login_required
def delete():
    device_mgr.delete_device(request.json['id'])
    return jsonify({"success": True})