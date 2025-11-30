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

    def edit_device(self, device_id, name, ip, ssh_user, ssh_pass, mac): # ✨ 增加 mac 参数
            for d in self.devices:
                if str(d['id']) == str(device_id):
                    d['name'] = name
                    d['ip'] = ip
                    d['ssh_user'] = ssh_user
                    d['ssh_pass'] = ssh_pass
                    d['mac'] = mac # ✨ 保存 MAC 到数据库
                    self.save_devices()
                    return True
            return False

    def add_device(self, name, ip):
        new_device = {
            "id": len(self.devices) + 1,
            "name": name, "ip": ip, "mac": self.resolve_mac(ip) or "",
            "ssh_user": "", "ssh_pass": "",
            # 扩展硬件信息字段
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

# ✨ 修复版：自动兼容 GBK/UTF-8 编码
    def fetch_hardware_info(self, device_id):
        dev = next((d for d in self.devices if str(d['id']) == str(device_id)), None)
        if not dev or not dev.get('ssh_user'):
            return False, "SSH 未配置，请点击编辑按钮填写账号密码"

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(dev['ip'], username=dev['ssh_user'], password=dev['ssh_pass'], timeout=5)
            
            # 定义 PowerShell 命令
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
                
                # --- 核心修复开始：智能解码 ---
                try:
                    # 1. 优先尝试 GBK (针对中文 Windows)
                    decoded_str = raw_bytes.decode('gbk').strip()
                except UnicodeDecodeError:
                    try:
                        # 2. 如果失败，尝试 UTF-8
                        decoded_str = raw_bytes.decode('utf-8').strip()
                    except:
                        # 3. 实在不行，强制忽略错误，防止崩溃
                        decoded_str = raw_bytes.decode('utf-8', errors='ignore').strip()
                # --- 核心修复结束 ---

                results[key] = decoded_str

            # 更新数据
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
            send_magic_packet(dev['mac'])
            return True, "WOL 信号已发送"
        
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