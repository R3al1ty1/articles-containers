import docker
import random
import string
import socket

def get_free_port():
    """Возвращает свободный порт на хосте."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def launch_chrome_container():
    client = docker.from_env()
    
    random_tag = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    container_name = f"chrome_container_{random_tag}"
    
    host_port_novnc = get_free_port()
    host_port_squid = get_free_port()
    
    image, build_logs = client.images.build(path=".", tag="chrome-vnc")
    
    container = client.containers.run(
        image.id,
        name=container_name,
        ports={
            '6080/tcp': host_port_novnc,
            '3128/tcp': host_port_squid,
        },
        environment={
            'DISPLAY': ':99'
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
        }
    }

if __name__ == "__main__":
    container_info = launch_chrome_container()
    print("Контейнер запущен:")
    print(container_info)