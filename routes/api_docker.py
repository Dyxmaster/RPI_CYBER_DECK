# routes/api_docker.py
from flask import Blueprint, jsonify, request
from modules import docker_ctl

bp = Blueprint('api_docker', __name__)


@bp.route('/api/docker/list')
def docker_list():
    return jsonify(docker_ctl.get_containers())


@bp.route('/api/docker/<action>/<cid>', methods=['GET'])  # 你现在前端用的是 GET
def docker_action(action, cid):
    """
    支持的 action:
    - start
    - stop
    - restart
    - delete / remove   （两个都接受）
    """
    if action == 'restart':
        ok, msg = docker_ctl.restart_container(cid)
    elif action == 'stop':
        ok, msg = docker_ctl.stop_container(cid)
    elif action == 'start':
        ok, msg = docker_ctl.start_container(cid)
    elif action in ('delete', 'remove'):
        # ✅ 真正删除容器
        ok, msg = docker_ctl.remove_container(cid)
    else:
        return jsonify({"status": "error", "msg": f"未知操作: {action}"}), 400

    status = "ok" if ok else "error"
    code = 200 if ok else 500
    return jsonify({"status": status, "msg": msg}), code

@bp.route('/api/docker/run', methods=['POST'])
def docker_run():
    """
    Body: { "image": "nginx:latest", "name": "my-nginx" }
    返回: { "success": bool, "msg": str, "container": str | null }
    """
    data = request.get_json(silent=True) or {}
    image = (data.get("image") or "").strip()
    name = (data.get("name") or "").strip() or None

    if not image:
        return jsonify({"success": False, "msg": "镜像名称不能为空。"}), 400

    ok, msg, container_name = docker_ctl.pull_and_run_container(image, name)
    code = 200 if ok else 500
    return jsonify({
        "success": ok,
        "msg": msg,
        "container": container_name
    }), code



#  新增：镜像 API ---

@bp.route('/api/docker/images')
def docker_images_list():
    return jsonify(docker_ctl.get_images())

@bp.route('/api/docker/image/delete', methods=['POST'])
def docker_image_delete():
    """
    Body: { "id": "image_short_id" }
    """
    data = request.get_json(silent=True) or {}
    img_id = data.get("id")
    
    if not img_id:
        return jsonify({"success": False, "msg": "Image ID required"}), 400
        
    ok, msg = docker_ctl.remove_image(img_id)
    return jsonify({"success": ok, "msg": msg})