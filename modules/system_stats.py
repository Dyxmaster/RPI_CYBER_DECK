import psutil
import time
import platform
import socket

def get_system_stats():
    # 1. CPU 信息
    cpu_percent = psutil.cpu_percent(interval=None) 
    
    cpu_freq = 0
    if psutil.cpu_freq():
        cpu_freq = round(psutil.cpu_freq().current, 0)
    
    # 2. 内存信息
    mem = psutil.virtual_memory()
    
    # 3. 磁盘信息
    disk = psutil.disk_usage('/')
    
    # 4. 温度
    temp = 0
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = round(int(f.read()) / 1000, 1)
    except:
        temps = psutil.sensors_temperatures()
        if 'cpu_thermal' in temps:
            temp = temps['cpu_thermal'][0].current

    # 5. 网络信息
    hostname = socket.gethostname()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
    except:
        ip_address = "127.0.0.1"

    # 6. 启动时间
    uptime_seconds = int(time.time() - psutil.boot_time())

    return {
        "cpu": {
            "usage": cpu_percent,
            "freq": cpu_freq,
            "cores": psutil.cpu_count()
        },
        "memory": {
            "total": round(mem.total / (1024**3), 1),
            "used": round(mem.used / (1024**3), 1),
            "percent": mem.percent
        },
        "disk": {
            "percent": disk.percent,
            "free": round(disk.free / (1024**3), 1)
        },
        "system": {
            "temp": temp,
            "hostname": hostname,
            "ip": ip_address,
            "os": platform.system() + " " + platform.release(),
            "uptime": uptime_seconds
        }
    }