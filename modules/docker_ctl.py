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
