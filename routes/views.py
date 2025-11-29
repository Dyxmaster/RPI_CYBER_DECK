from flask import Blueprint, render_template

# 创建蓝图
bp = Blueprint('views', __name__)

@bp.route('/')
def index():
    """系统概览页"""
    return render_template('index.html', active_page='dashboard', initial_tab='dashboard')

@bp.route('/containers')
def page_containers():
    """容器管理页"""
    return render_template('containers.html', active_page='containers')