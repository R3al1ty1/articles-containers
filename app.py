import docker
from flask import Flask, redirect, request, jsonify
import random
import string
import socket
from werkzeug.serving import run_simple
import re

app = Flask(__name__)
client = docker.from_env()

def get_free_port():
    """Возвращает свободный порт на хосте."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def launch_chrome_container():
    """Запускает контейнер с Chrome и возвращает его tag и порты."""
    random_tag = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    container_name = f"chrome_container_{random_tag}"
    
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

@app.route('/create', methods=['GET'])
def create_container():
    """Создает новый контейнер и возвращает его информацию."""
    container_info = launch_chrome_container()
    tag = container_info["random_tag"]
    
    # Возвращаем URL для доступа к контейнеру
    container_url = f"http://localhost:8000/{tag}"
    return jsonify({
        "container_info": container_info,
        "access_url": container_url
    })

@app.route('/<random_tag>', methods=['GET'])
def access_container(random_tag):
    """Перенаправляет на noVNC порт соответствующего контейнера."""
    container_info = find_container_by_tag(random_tag)
    
    if not container_info:
        return "Контейнер не найден или не запущен", 404
    
    novnc_port = container_info["host_ports"]["noVNC"]
    
    if not novnc_port:
        return "Порт noVNC не найден для данного контейнера", 404
    
    # Получаем внешний хост из заголовков запроса (например, scopus-containers.baixo.keenetic.pro:8443)
    # Если используется обратный прокси, можно опираться на X-Forwarded-Host
    external_host = request.headers.get('X-Forwarded-Host', request.host)
    
    # Определяем схему: если запрос пришел через HTTPS (например, обратный прокси добавил X-Forwarded-Proto),
    # то используем её, иначе берём из запроса.
    scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
    
    # Здесь формируем URL, где вместо localhost подставляем внешний хост.
    # Внимание: убедитесь, что случайный порт (novnc_port) действительно доступен извне.
    target_url = f"{scheme}://{external_host.split(':')[0]}:{novnc_port}"
    
    return redirect(target_url)

@app.route('/containers', methods=['GET'])
def list_containers():
    """Возвращает список всех запущенных контейнеров Chrome."""
    containers = find_all_chrome_containers()
    return jsonify(containers)

@app.route('/', methods=['GET'])
def index():
    """Домашняя страница с ссылками на все контейнеры."""
    containers = find_all_chrome_containers()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chrome Containers</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; }
            ul { list-style-type: none; padding: 0; }
            li { margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .button { display: inline-block; padding: 10px 15px; background-color: #0066cc; color: white; 
                     border-radius: 4px; text-decoration: none; margin-top: 20px; }
            .button:hover { background-color: #0055aa; }
        </style>
    </head>
    <body>
        <h1>Chrome Containers</h1>
        <a href="/create" class="button">Create New Container</a>
        <h2>Active Containers:</h2>
        <ul>
    """
    
    for container in containers:
        tag = container.get("random_tag")
        name = container.get("container_name")
        novnc_port = container.get("host_ports", {}).get("noVNC")
        
        if tag and novnc_port:
            html += f"""
            <li>
                <strong>{name}</strong> (Tag: {tag})<br>
                noVNC Port: {novnc_port}<br>
                <a href="/{tag}">Access Container</a> | 
                <a href="http://localhost:{novnc_port}" target="_blank">Direct noVNC Link</a>
            </li>
            """
    
    html += """
        </ul>
    </body>
    </html>
    """
    
    return html

if __name__ == '__main__':
    # Запускаем Flask сервер на порту 8000
    run_simple('0.0.0.0', 8000, app, use_reloader=True)