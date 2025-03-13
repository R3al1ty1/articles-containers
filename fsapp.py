import shutil
import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from containers import (
    find_all_chrome_containers,
    find_container_by_tag,
    launch_chrome_container
)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/create")
def create_container():
    """Создает новый контейнер и возвращает его информацию."""
    container_info = launch_chrome_container()
    tag = container_info["random_tag"]
    return {
        "container_info": container_info,
        "access_url": f"http://147.45.241.240:8000/{tag}"
    }


@app.get("/{random_tag}")
def access_container(random_tag: str, request: Request):
    """Перенаправляет на noVNC порт контейнера."""
    container_info = find_container_by_tag(random_tag)
    if not container_info:
        raise HTTPException(404, "Контейнер не найден или не запущен")

    novnc_port = container_info["host_ports"].get("noVNC")
    if not novnc_port:
        raise HTTPException(404, "Порт noVNC не найден")

    scheme = request.headers.get("X-Forwarded-Proto", "http")
    host = request.headers.get("X-Forwarded-Host", request.url.hostname)
    target_url = f"{scheme}://{host.split(':')[0]}:{novnc_port}/vnc.html?autoconnect=true&resize=scale"

    return RedirectResponse(target_url)


@app.get("/containers")
def list_containers():
    """Возвращает список всех запущенных контейнеров."""
    return find_all_chrome_containers()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Главная страница со списком контейнеров."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "containers": find_all_chrome_containers()}
    )


@app.delete("/delete-directory/{random_tag}")
def delete_directory(random_tag: str):
    """Удаляет директорию контейнера по его тегу."""
    container_info = find_container_by_tag(random_tag)
    if not container_info:
        raise HTTPException(404, "Контейнер не найден")

    dir_path = (os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                + random_tag)

    if not dir_path or not os.path.exists(dir_path):
        raise HTTPException(404, "Директория не найдена")

    try:
        shutil.rmtree(dir_path)
        return {"status": "success", "message": "Директория удалена"}
    except Exception as e:
        raise HTTPException(500, f"Ошибка удаления: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
