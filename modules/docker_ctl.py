# modules/docker_ctl.py
import docker
import time
import json

try:
    client = docker.from_env()
except Exception as e:
    print(f"Docker connection failed: {e}")
    client = None


def get_containers():
    if not client:
        return []

    container_list = []
    try:
        for c in client.containers.list(all=True):
            container_list.append({
                'id': c.short_id,
                'name': c.name,
                'status': c.status,
                'image': c.image.tags[0] if c.image.tags else 'none'
            })
    except Exception as e:
        print(f"Error fetching containers: {e}")
        return []

    return container_list


def restart_container(container_id):
    if not client:
        return False, "Docker 客户端未连接"
    try:
        container = client.containers.get(container_id)
        container.restart()
        return True, "容器已重启"
    except docker.errors.NotFound:
        return False, "容器未找到"
    except Exception as e:
        return False, f"重启失败: {e}"


def stop_container(container_id):
    if not client:
        return False, "Docker 客户端未连接"
    try:
        container = client.containers.get(container_id)
        container.stop()
        return True, "容器已停止"
    except docker.errors.NotFound:
        return False, "容器未找到"
    except Exception as e:
        return False, f"停止失败: {e}"


def start_container(container_id):
    if not client:
        return False, "Docker 客户端未连接"
    try:
        container = client.containers.get(container_id)
        container.start()
        return True, "容器已启动"
    except docker.errors.NotFound:
        return False, "容器未找到"
    except Exception as e:
        return False, f"启动失败: {e}"


def remove_container(container_id):
    if not client:
        return False, "Docker 客户端未连接"
    try:
        container = client.containers.get(container_id)
        container.remove(force=True, v=True)
        return True, "容器已删除"
    except docker.errors.NotFound:
        return False, "容器未找到"
    except Exception as e:
        return False, f"删除失败: {e}"


def pull_and_run_container(image_name, container_name=None):
    """始终返回 (ok, msg, container_name)"""
    if not client:
        return False, "Docker 客户端未连接", None
    try:
        # 拉取镜像
        client.images.pull(image_name)

        # 运行容器
        container = client.containers.run(
            image=image_name,
            detach=True,
            name=container_name or None
        )
        return True, f"镜像 {image_name} 已运行", container.name
    except docker.errors.ImageNotFound:
        return False, f"镜像 {image_name} 未找到，请检查名称或 tag。", None
    except docker.errors.APIError as e:
        # 有些 APIError 没有 explanation 字段，小心处理一下
        explanation = getattr(e, "explanation", str(e))
        first_line = explanation.splitlines()[0] if explanation else str(e)
        return False, f"Docker API 错误: {first_line}", None
    except Exception as e:
        return False, f"运行容器失败: {e}", None



# --- 镜像管理功能 ---

def get_images():
    if not client:
        return []
    
    images_list = []
    try:
        for img in client.images.list():
            # Docker 镜像大小是字节，转换成 MB
            size_mb = round(img.attrs.get('Size', 0) / (1024 * 1024), 2)
            created = img.attrs.get('Created', '').split('T')[0] # 简单截取日期
            
            # 一个镜像可能有多个 Tag (例如 nginx:latest 和 nginx:1.21 可能是同一个 ID)
            # 如果没有 Tag (悬空镜像)，显示为 <none>
            tags = img.tags if img.tags else ['<none>:<none>']
            
            for tag in tags:
                images_list.append({
                    'id': img.short_id.split(':')[-1], # 去掉 sha256: 前缀
                    'tag': tag,
                    'size': f"{size_mb} MB",
                    'created': created
                })
    except Exception as e:
        print(f"Error fetching images: {e}")
        return []
        
    return images_list

def remove_image(image_id):
    if not client:
        return False, "Docker 客户端未连接"
    try:
        # force=True 强制删除，防止有停止的容器占用无法删除
        client.images.remove(image_id, force=True) 
        return True, "镜像已删除"
    except docker.errors.ImageNotFound:
        return False, "镜像未找到"
    except Exception as e:
        # 处理 Docker 返回的错误信息
        err_str = str(e)
        if "conflict" in err_str.lower():
            return False, "删除失败：镜像正在被运行中的容器使用"
        return False, f"删除失败: {e}"