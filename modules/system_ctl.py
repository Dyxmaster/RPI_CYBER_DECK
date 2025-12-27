import subprocess
import os

def is_docker():
    """简单的环境检测，检查 /.dockerenv 是否存在"""
    return os.path.exists('/.dockerenv')

def run_host_cmd(cmd_list):
    """
    执行系统命令
    """
    # 如果在 Docker 容器内，使用 nsenter 穿透
    # 注意：这依然需要容器开启 --privileged --pid=host
    if is_docker():
        full_cmd = ['nsenter', '--target', '1', '--mount', '--uts', '--ipc', '--net', '--pid', '--'] + cmd_list
    else:
        # 如果是直接在宿主机跑 (比如用 systemd)，直接 sudo 执行
        # 确保运行该脚本的用户有 sudo 权限且免密
        full_cmd = ['sudo'] + cmd_list

    try:
        # text=True 让 stdout 返回字符串而不是 bytes
        result = subprocess.run(full_cmd, check=True, capture_output=True, text=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip() if e.stderr else str(e)
    except Exception as e:
        return False, str(e)

# 下面的函数保持不变...
def shutdown():
    return run_host_cmd(['shutdown', '-h', 'now'])

def reboot():
    return run_host_cmd(['reboot'])

def scan_wifi():
    # 之前提供的 scan_wifi 代码...
    # (保持你上一条消息里的 scan_wifi 逻辑即可)
    cmd = ['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY,IN-USE', 'dev', 'wifi', 'list']
    success, output = run_host_cmd(cmd)
    
    if not success:
        return False, output

    networks = []
    seen_ssids = set()

    for line in output.split('\n'):
        if not line: continue
        parts = line.split(':')
        if len(parts) < 3: continue
        
        in_use = parts[-1]
        security = parts[-2]
        signal = parts[-3]
        ssid = ":".join(parts[:-3]) 
        
        if not ssid: continue
        
        if ssid not in seen_ssids:
            seen_ssids.add(ssid)
            networks.append({
                "ssid": ssid,
                "signal": signal,
                "security": security,
                "active": in_use == '*'
            })
            
    networks.sort(key=lambda x: int(x['signal']), reverse=True)
    return True, networks

def connect_wifi(ssid, password):
    # --- 修改开始 ---
    # 如果有密码，拼接带密码的命令
    if password:
        cmd = ['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password]
    else:
        # 如果密码为空（Open 网络），直接连接 SSID，不带 password 参数
        cmd = ['nmcli', 'dev', 'wifi', 'connect', ssid]
    # --- 修改结束 ---
    
    return run_host_cmd(cmd)