from flask import Blueprint, render_template
from flask_login import login_required  # 1. 导入

bp = Blueprint('views', __name__)

@bp.route('/')
@login_required  # 2. 加上这个装饰器
def index():
    return render_template('index.html', active_page='dashboard')

@bp.route('/containers')
@login_required  # 2. 加上这个装饰器
def containers():
    return render_template('containers.html', active_page='containers')