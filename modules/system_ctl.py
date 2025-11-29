import subprocess

def run_host_cmd(cmd_list):
    """
    使用 nsenter 进入宿主机命名空间执行命令
    前提: Docker 容器启动时必须加 --privileged --pid=host
    """
    # 组合命令：nsenter -t 1 -m -u -i -n -p -- <你的命令>
    full_cmd = ['nsenter', '--target', '1', '--mount', '--uts', '--ipc', '--net', '--pid', '--'] + cmd_list
    try:
        subprocess.run(full_cmd, check=True)
        return True, "命令已发送"
    except Exception as e:
        return False, str(e)

def shutdown():
    # 发送关机命令
    return run_host_cmd(['shutdown', '-h', 'now'])

def reboot():
    # 发送重启命令
    return run_host_cmd(['reboot'])