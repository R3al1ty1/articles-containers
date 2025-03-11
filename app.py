import shutil
import os
from flask import Flask, redirect, request, jsonify
from werkzeug.serving import run_simple

from containers import (
    find_all_chrome_containers,
    find_container_by_tag,
    launch_chrome_container
)


app = Flask(__name__)


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

    external_host = request.headers.get('X-Forwarded-Host', request.host)

    scheme = request.headers.get('X-Forwarded-Proto', request.scheme)

    target_url = f"{scheme}://{external_host.split(':')[0]}:{novnc_port}/vnc.html?autoconnect=true&resize=scale"

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
