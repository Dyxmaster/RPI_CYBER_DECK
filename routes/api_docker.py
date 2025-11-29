from flask import Blueprint, jsonify
from modules import docker_ctl

bp = Blueprint('api_docker', __name__)

@bp.route('/api/docker/list')
def docker_list():
    return jsonify(docker_ctl.get_containers())

@bp.route('/api/docker/<action>/<cid>')
def docker_action(action, cid):
    result = False
    if action == 'restart':
        result = docker_ctl.restart_container(cid)
    elif action == 'stop':
        result = docker_ctl.stop_container(cid)
    elif action == 'start':
        result = docker_ctl.start_container(cid)
    
    if result:
        return jsonify({"status": "ok", "msg": f"Container {cid} {action}ed"})
    else:
        return jsonify({"status": "error", "msg": "Action failed"}), 500