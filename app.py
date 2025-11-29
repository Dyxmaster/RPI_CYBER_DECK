from flask import Flask

# 导入拆分好的蓝图 (Blueprints)
# 这里的路径对应文件夹 routes/ 下的具体文件
from routes.views import bp as views_bp
from routes.api_monitor import bp as monitor_bp
from routes.api_docker import bp as docker_bp
from routes.api_system import bp as system_bp  # ✨ 修正：使用 system_bp 作为系统 API 的别名

app = Flask(__name__)

# --- 注册蓝图 ---
# 将各个模块的功能挂载到主程序上
app.register_blueprint(views_bp)        # 页面路由 (/, /network, /containers 等)
app.register_blueprint(monitor_bp)      # 硬件监控 API (/api/stats)
app.register_blueprint(docker_bp)       # Docker 控制 API (/api/docker/...)
app.register_blueprint(system_bp)       # ✨ 注册系统控制 API (/api/system/...)

if __name__ == '__main__':
    print(">>> RPI_CORE 系统启动中...")
    print(">>> 模块加载状态: [视图层: OK] [监控层: OK] [Docker层: OK] [系统控制层: OK]") 
    
    # 启动 Flask 服务
    # port=6030 是您指定的端口
    app.run(host='0.0.0.0', port=6030, debug=True)