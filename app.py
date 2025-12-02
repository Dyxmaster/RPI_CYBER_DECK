from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# 1. 导入配置
from config import Config

# 2. 导入蓝图 (Blueprints)
from routes.views import bp as views_bp
from routes.api_monitor import bp as monitor_bp
from routes.api_docker import bp as docker_bp
from routes.api_system import bp as system_bp
from routes.api_devices import bp_devices

# [新增] 导入 NEXUS 蓝图
from routes.api_nexus import bp_nexus

app = Flask(__name__)

# 3. 应用配置
app.config.from_object(Config)

# --- 4. 初始化登录管理器 ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

# --- 5. 用户模型 ---
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == Config.ADMIN_USER:
        return User(user_id)
    return None

# --- 6. 核心路由 ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == Config.ADMIN_USER and password == Config.ADMIN_PASS:
            user = User(username)
            login_user(user)
            return redirect(url_for('views.index'))
        else:
            flash('ACCESS DENIED // 账号或密码错误')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# [新增] NEXUS 页面路由
@app.route('/nexus')
@login_required
def nexus_page():
    # active_page 参数用于控制左侧导航栏的高亮 (如果你 nav.html 里做了逻辑)
    return render_template('nexus.html', active_page='nexus')

# --- 7. 注册蓝图 ---
app.register_blueprint(views_bp)
app.register_blueprint(monitor_bp)
app.register_blueprint(docker_bp)
app.register_blueprint(system_bp)
app.register_blueprint(bp_devices)

# [新增] 注册 NEXUS 蓝图
app.register_blueprint(bp_nexus)

if __name__ == '__main__':
    print(">>> RPI_CORE 安全系统启动中...")
    print(">>> 模块加载状态: [视图: OK] [监控: OK] [Docker: OK] [系统: OK] [设备: OK] [NEXUS: OK]") 
    
    # ⚠️ 重要：必须使用 6030 端口，因为你的 Dockerfile EXPOSE 6030
    app.run(host='0.0.0.0', port=5000, debug=True)