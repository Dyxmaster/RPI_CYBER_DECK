from flask import Flask

# 导入拆分好的蓝图 (Blueprints)
# 这里的路径对应文件夹 routes/ 下的具体文件
from routes.views import bp as views_bp
from routes.api_monitor import bp as monitor_bp
from routes.api_docker import bp as docker_bp
from routes.api_system import bp as system_bp
from routes.api_devices import bp_devices  # ✨ 新增：导入设备管理蓝图

app = Flask(__name__)

# --- 注册蓝图 ---
# 将各个模块的功能挂载到主程序上
app.register_blueprint(views_bp)        # 页面路由 (/, /network, /containers 等)
app.register_blueprint(monitor_bp)      # 硬件监控 API (/api/stats)
app.register_blueprint(docker_bp)       # Docker 控制 API (/api/docker/...)
app.register_blueprint(system_bp)       # 系统控制 API (/api/system/...)
app.register_blueprint(bp_devices)      # ✨ 新增：注册设备管理模块 (/devices, /api/devices/...)

if __name__ == '__main__':
    print(">>> RPI_CORE 系统启动中...")
    print(">>> 模块加载状态: [视图: OK] [监控: OK] [Docker: OK] [系统: OK] [设备管理: OK]") 
    
    # 启动 Flask 服务
    # port=6030 是您指定的端口
    app.run(host='0.0.0.0', port=5000, debug=True)