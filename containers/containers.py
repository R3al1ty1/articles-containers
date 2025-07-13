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


def launch_chrome_container(website: str):
    """
    Запускает контейнер с Chrome и возвращает его tag и порты.
    Поддерживаемые значения для website: 'scopus', 'wos'.
    """
    if website not in ['scopus', 'wos']:
        raise ValueError("Неподдерживаемый сайт. Используйте 'scopus' или 'wos'.")

    image_tag = "chrome-vnc-custom"

    try:
        client.images.get(image_tag)
    except docker.errors.ImageNotFound:
        print(f"Образ {image_tag} не найден. Собираем...")
        build_context_path = "/app/chrome_builder"
        client.images.build(path=build_context_path, tag=image_tag)
        print("Сборка завершена.")


    random_tag = ''.join(
        random.choices(
            string.ascii_lowercase + string.digits, k=8
        )
    )

    container_name = f"chrome_container_{website}_{random_tag}"
    downloads_dir = os.path.join("/root", "Downloads", random_tag)

    os.makedirs(downloads_dir, exist_ok=True)

    host_port_novnc = get_free_port()
    host_port_squid = get_free_port()

    container = client.containers.run(
        image_tag,
        name=container_name,
        ports={
            '6080/tcp': host_port_novnc,
            '3128/tcp': host_port_squid,
        },
        environment={
            'DISPLAY': ':99',
            'WEBSITE_TARGET': website
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
        "website": website,
        "host_ports": {
            "noVNC": host_port_novnc,
            "squid": host_port_squid
        },
        "downloads_path": os.path.abspath(downloads_dir)
    }


def extract_tag_from_name(name):
    """Извлекает tag из имени контейнера."""
    match = re.search(r'chrome_container_.+?_([a-z0-9]{8})$', name)
    if match:
        return match.group(1)
    return None


def find_container_by_tag(tag):
    """Находит контейнер по тегу используя имя контейнера."""
    containers = client.containers.list()

    for container in containers:
        if tag in container.name:
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
        if container.name.startswith('chrome_container'):
            tag = extract_tag_from_name(container.name)

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
    container_info = launch_chrome_container(website="wos")
    print("Контейнер запущен:")
    print(container_info)
