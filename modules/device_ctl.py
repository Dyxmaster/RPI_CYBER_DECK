import os
import json
import subprocess
import paramiko
import re
from wakeonlan import send_magic_packet

DATA_FILE = 'devices.json'

class DeviceManager:
    def __init__(self):
        self.devices = self.load_devices()

    def load_devices(self):
        if not os.path.exists(DATA_FILE): return []
        with open(DATA_FILE, 'r') as f: return json.load(f)

    def save_devices(self):
        with open(DATA_FILE, 'w') as f: json.dump(self.devices, f, indent=4)

    # --- ✨ 新增：穿透 Docker 执行宿主机命令的辅助函数 ---
    def run_host_cmd(self, cmd_list):
        """
        判断是否在 Docker 中，如果是，则使用 nsenter 穿透到宿主机执行命令。
        """
        # 判断是否在 Docker 环境 (检查 /.dockerenv 文件)
        is_docker = os.path.exists('/.dockerenv')
        
        if is_docker:
            # Docker 模式：使用 nsenter 进入宿主机 (PID 1) 的命名空间
            # 注意：这要求 Docker 容器启动时加了 --privileged 和 --pid=host 参数
            prefix = ['nsenter', '--target', '1', '--mount', '--uts', '--ipc', '--net', '--pid', '--']
            full_cmd = prefix + cmd_list
        else:
            # 裸机模式：直接使用 sudo
            full_cmd = ['sudo'] + cmd_list

        try:
            # 执行命令
            subprocess.run(full_cmd, check=True, capture_output=True, text=True)
            return True, "执行成功"
        except subprocess.CalledProcessError as e:
            return False, f"命令失败: {e.stderr.strip() if e.stderr else str(e)}"
        except Exception as e:
            return False, f"执行错误: {str(e)}"
    # ------------------------------------------------

    def edit_device(self, device_id, name, ip, ssh_user, ssh_pass, mac): 
            for d in self.devices:
                if str(d['id']) == str(device_id):
                    d['name'] = name
                    d['ip'] = ip
                    d['ssh_user'] = ssh_user
                    d['ssh_pass'] = ssh_pass
                    d['mac'] = mac 
                    self.save_devices()
                    return True
            return False

    def add_device(self, name, ip):
        new_device = {
            "id": len(self.devices) + 1,
            "name": name, "ip": ip, "mac": self.resolve_mac(ip) or "",
            "ssh_user": "", "ssh_pass": "",
            "cpu_name": "Unknown", "gpu_name": "Unknown",
            "ram_size": "Unknown", "os_ver": "Unknown"
        }
        self.devices.append(new_device)
        self.save_devices()
        return new_device

    def delete_device(self, device_id):
        self.devices = [d for d in self.devices if str(d['id']) != str(device_id)]
        self.save_devices()

    def get_ping_status(self, ip):
        try:
            output = subprocess.check_output(['ping', '-c', '1', '-W', '1', ip], stderr=subprocess.STDOUT).decode()
            match = re.search(r'time=([\d\.]+)', output)
            return {"online": True, "latency": match.group(1) if match else "<1"}
        except:
            return {"online": False, "latency": 0}

    def fetch_hardware_info(self, device_id):
        dev = next((d for d in self.devices if str(d['id']) == str(device_id)), None)
        if not dev or not dev.get('ssh_user'):
            return False, "SSH 未配置，请点击编辑按钮填写账号密码"

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(dev['ip'], username=dev['ssh_user'], password=dev['ssh_pass'], timeout=5)
            
            cmds = {
                "cpu": 'powershell "(Get-CimInstance Win32_Processor).Name"',
                "gpu": 'powershell "Get-CimInstance Win32_VideoController | Where-Object { $_.Name -notmatch \'Virtual|GameViewer|Remote|DisplayLink\' } | Sort-Object @{Expression={$_.Name -match \'NVIDIA|AMD|Radeon|Arc\'}; Ascending=$false} | Select-Object -First 1 -ExpandProperty Name"',
                "ram": 'powershell "[math]::Round((Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum / 1GB, 0)"',
                "os":  'powershell "(Get-CimInstance Win32_OperatingSystem).Caption"'
            }

            results = {}
            for key, cmd in cmds.items():
                stdin, stdout, stderr = ssh.exec_command(cmd)
                raw_bytes = stdout.read()
                try:
                    decoded_str = raw_bytes.decode('gbk').strip()
                except UnicodeDecodeError:
                    try:
                        decoded_str = raw_bytes.decode('utf-8').strip()
                    except:
                        decoded_str = raw_bytes.decode('utf-8', errors='ignore').strip()
                results[key] = decoded_str

            dev['cpu_name'] = results.get('cpu', 'N/A')
            dev['gpu_name'] = results.get('gpu', 'N/A')
            dev['ram_size'] = f"{results.get('ram', '?')} GB"
            dev['os_ver'] = results.get('os', 'Windows').replace("Microsoft ", "")

            self.save_devices()
            ssh.close()
            return True, "硬件信息同步完成"
        except Exception as e:
            return False, f"SSH 错误: {str(e)}"

    def power_control(self, device_id, action):
        dev = next((d for d in self.devices if str(d['id']) == str(device_id)), None)
        if not dev: return False, "设备不存在"

        if action == 'wake':
            if not dev['mac']: return False, "MAC 地址未知"
            
            # --- ✨ 修改：使用 run_host_cmd 穿透到宿主机执行 etherwake ---
            # 这样就会调用宿主机上的 etherwake，利用宿主机的 eth0 发送
            success, msg = self.run_host_cmd(['etherwake', '-i', 'eth0', dev['mac']])
            
            if success:
                return True, "WOL (Host-Etherwake) 发送成功"
            else:
                # 如果穿透失败（比如没权限），回退到普通广播
                print(f"Etherwake failed: {msg}, trying broadcast...")
                try:
                    send_magic_packet(dev['mac'])
                    return True, "Etherwake 失败，已使用广播模式"
                except Exception as e:
                    return False, f"WOL 发送失败: {str(e)}"
            # ----------------------------------------------------------
        
        if not dev.get('ssh_user'): return False, "SSH 未配置"

        cmd = "shutdown /s /t 0" if action == 'shutdown' else "shutdown /r /t 0"
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(dev['ip'], username=dev['ssh_user'], password=dev['ssh_pass'], timeout=3)
            ssh.exec_command(cmd)
            ssh.close()
            return True, f"指令 {action} 发送成功"
        except Exception as e:
            return False, f"SSH 失败: {str(e)}"

    def resolve_mac(self, ip):
        try:
            subprocess.run(['ping', '-c', '1', '-W', '1', ip], stdout=subprocess.DEVNULL)
            with open('/proc/net/arp', 'r') as f:
                for line in f.readlines()[1:]:
                    if line.startswith(ip + " "): return line.split()[3]
        except: return None
        return None

device_mgr = DeviceManager()