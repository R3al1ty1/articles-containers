import docker
import random
import string
import socket
import re
import os
import shutil


client = docker.from_env()


def get_free_port():
    """Возвращает свободный порт на хосте."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def launch_chrome_container():
    """Запускает контейнер с Chrome и возвращает его tag и порты."""
    random_tag = ''.join(
        random.choices(
            string.ascii_lowercase + string.digits, k=8
        )
    )

    container_name = f"chrome_container_{random_tag}"

    downloads_dir = os.path.join("downloads", random_tag)
    os.makedirs(downloads_dir, exist_ok=True)

    host_port_novnc = get_free_port()
    host_port_squid = get_free_port()

    image, build_logs = client.images.build(path=".", tag="chrome-vnc")

    container = client.containers.run(
        "chrome-vnc",
        name=container_name,
        ports={
            '6080/tcp': host_port_novnc,
            '3128/tcp': host_port_squid,
        },
        environment={
            'DISPLAY': ':99'
        },
        volumes={
            os.path.abspath(downloads_dir): {
                'bind': '/root/Downloads',
                'mode': 'rw'
            }
        },
        detach=True
    )

    return {
        "container_id": container.id,
        "container_name": container_name,
        "random_tag": random_tag,
        "host_ports": {
            "noVNC": host_port_novnc,
            "squid": host_port_squid
        },
        "downloads_path": os.path.abspath(downloads_dir)
    }


def extract_tag_from_name(name):
    """Извлекает tag из имени контейнера."""
    match = re.search(r'chrome_container_([a-z0-9]+)$', name)
    if match:
        return match.group(1)
    return None


def find_container_by_tag(tag):
    """Находит контейнер по тегу используя имя контейнера."""
    # Ищем среди всех запущенных контейнеров
    containers = client.containers.list()

    for container in containers:
        # Проверяем, содержит ли имя контейнера наш тег
        if tag in container.name:
            # Получаем порты контейнера
            container_data = client.api.inspect_container(container.id)
            port_mappings = container_data['NetworkSettings']['Ports']

            novnc_port = None
            if '6080/tcp' in port_mappings and port_mappings['6080/tcp']:
                novnc_port = port_mappings['6080/tcp'][0]['HostPort']

            squid_port = None
            if '3128/tcp' in port_mappings and port_mappings['3128/tcp']:
                squid_port = port_mappings['3128/tcp'][0]['HostPort']

            return {
                "container_id": container.id,
                "container_name": container.name,
                "random_tag": tag,
                "host_ports": {
                    "noVNC": novnc_port,
                    "squid": squid_port
                }
            }

    return None


def stop_container(container_info):
    try:
        container = client.containers.get(container_info["container_id"])

        container.stop()
        container.remove(force=True)

    except docker.errors.NotFound:
        return {"status": "error", "message": "Контейнер уже был удален"}


def find_all_chrome_containers():
    """Находит все контейнеры Chrome на основе имени."""
    containers = client.containers.list()

    result = []
    for container in containers:
        # Если имя контейнера начинается с chrome_container
        if container.name.startswith('chrome_container'):
            tag = extract_tag_from_name(container.name)

            # Получаем порты контейнера
            container_data = client.api.inspect_container(container.id)
            port_mappings = container_data['NetworkSettings']['Ports']

            novnc_port = None
            if '6080/tcp' in port_mappings and port_mappings['6080/tcp']:
                novnc_port = port_mappings['6080/tcp'][0]['HostPort']

            squid_port = None
            if '3128/tcp' in port_mappings and port_mappings['3128/tcp']:
                squid_port = port_mappings['3128/tcp'][0]['HostPort']

            result.append({
                "container_id": container.id,
                "container_name": container.name,
                "random_tag": tag,
                "host_ports": {
                    "noVNC": novnc_port,
                    "squid": squid_port
                }
            })

    return result


if __name__ == "__main__":
    container_info = launch_chrome_container()
    print("Контейнер запущен:")
    print(container_info)
