from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# 1. 导入配置 (确保根目录下有 config.py)
from config import Config

# 导入拆分好的蓝图
from routes.views import bp as views_bp
from routes.api_monitor import bp as monitor_bp
from routes.api_docker import bp as docker_bp
from routes.api_system import bp as system_bp
from routes.api_devices import bp_devices

app = Flask(__name__)

# 2. 应用配置 (加载 SECRET_KEY 和 账号密码)
app.config.from_object(Config)

# --- 3. 初始化登录管理器 ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 未登录访问受保护页面时，自动跳到这个视图

# --- 4. 定义简单的用户模型 ---
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == Config.ADMIN_USER:
        return User(user_id)
    return None

# --- 5. 登录与注销路由 ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    # 如果已经登录，直接跳到首页
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 验证账号密码
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

# --- 6. 注册蓝图 ---
app.register_blueprint(views_bp)
app.register_blueprint(monitor_bp)
app.register_blueprint(docker_bp)
app.register_blueprint(system_bp)
app.register_blueprint(bp_devices)

if __name__ == '__main__':
    print(">>> RPI_CORE 安全系统启动中...")
    print(">>> 模块加载状态: [视图: OK] [监控: OK] [Docker: OK] [系统: OK] [设备管理: OK]") 
    
    # 启动 Flask 服务
    # ⚠️ 重要：必须使用 6030 端口，因为你的 Dockerfile EXPOSE 6030
    # 如果改成 5000，Docker 外部将无法访问！
    app.run(host='0.0.0.0', port=5000, debug=True)