from flask import Blueprint, jsonify, request
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

# --- 新增 WiFi 接口 ---

@bp.route('/api/wifi/scan', methods=['GET'])
@login_required
def wifi_scan():
    success, data = system_ctl.scan_wifi()
    if success:
        return jsonify({"status": "ok", "networks": data})
    else:
        return jsonify({"status": "error", "msg": f"扫描失败: {data}"}), 500

@bp.route('/api/wifi/connect', methods=['POST'])
@login_required
def wifi_connect():
    req_data = request.get_json()
    ssid = req_data.get('ssid')
    password = req_data.get('password')
    
    # --- 修改前 ---
    # if not ssid or not password:
    #    return jsonify({"status": "error", "msg": "缺少 SSID 或密码"}), 400

    # --- 修改后 ---
    # 只检查 SSID 是否存在，密码如果是空字符串也是允许的（针对 Open 网络）
    if not ssid:
        return jsonify({"status": "error", "msg": "缺少 SSID"}), 400

    success, msg = system_ctl.connect_wifi(ssid, password)
    
    if success:
        return jsonify({"status": "ok", "msg": f"成功连接到 {ssid}"})
    else:
        return jsonify({"status": "error", "msg": f"连接失败: {msg}"}), 500