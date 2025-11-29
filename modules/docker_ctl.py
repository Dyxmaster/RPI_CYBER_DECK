import docker
import time

# 连接到树莓派本地的 Docker 守护进程
try:
    client = docker.from_env()
except:
    client = None

def get_containers():
    if not client:
        return []
    
    container_list = []
    # 获取所有容器（包括停止的）
    for c in client.containers.list(all=True):
        container_list.append({
            'id': c.short_id,
            'name': c.name,
            'status': c.status, # running, exited, etc.
            'image': c.image.tags[0] if c.image.tags else 'none'
        })
    return container_list

def restart_container(container_id):
    if not client: return False
    try:
        container = client.containers.get(container_id)
        container.restart()
        return True
    except:
        return False

def stop_container(container_id):
    if not client: return False
    try:
        container = client.containers.get(container_id)
        container.stop()
        return True
    except:
        return False

def start_container(container_id):
    if not client: return False
    try:
        container = client.containers.get(container_id)
        container.start()
        return True
    except:
        return False