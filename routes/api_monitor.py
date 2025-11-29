# routes/api_monitor.py

from flask import Blueprint, jsonify
from modules.system_stats import get_system_stats  # 注意：从 modules.system_stats 导入

# 这个就是给 app.py 用的 bp
bp = Blueprint("api_monitor", __name__)

@bp.route("/api/system/stats")
def api_system_stats():
    """
    返回树莓派的实时系统状态（CPU / 内存 / 磁盘 / 温度 / IP 等）
    """
    stats = get_system_stats()
    return jsonify(stats)
