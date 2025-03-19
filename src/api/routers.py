import shutil
import os
import redis
from fastapi import Request, HTTPException, Depends, APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from containers import (
    find_all_chrome_containers,
    find_container_by_tag,
    launch_chrome_container
)
from src.core.database import get_redis


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/create/{user_id}")
def create_container(user_id: str, redis_db: redis.Redis = Depends(get_redis)):
    """Создает контейнер и связывает его с user_id в Redis"""
    if not user_id:
        raise HTTPException(400, "Требуется user_id")

    existing_tag = redis_db.get(f"user:{user_id}")
    if existing_tag:
        return {
            "status": "exists",
            "container_info": find_container_by_tag(existing_tag),
            "access_url": f"http://147.45.241.240:8000/access/{user_id}"
        }

    container_info = launch_chrome_container()
    tag = container_info["random_tag"]

    redis_db.setex(f"user:{user_id}", 86400, tag)

    return {
        "status": "created",
        "container_info": container_info,
        "access_url": f"http://147.45.241.240:8000/access/{user_id}"
    }


@router.get("/access/{user_id}")
def access_container(
    user_id: str,
    request: Request,
    redis_db: redis.Redis = Depends(get_redis)
):
    """Перенаправляет на контейнер пользователя через Redis"""
    if not user_id:
        raise HTTPException(400, "Требуется user_id")

    random_tag = redis_db.get(f"user:{user_id}")
    if not random_tag:
        raise HTTPException(404, "Контейнер не найден для данного пользователя")

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


@router.get("/containers")
def list_containers():
    """Возвращает список всех запущенных контейнеров."""
    return find_all_chrome_containers()


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Главная страница со списком контейнеров."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "containers": find_all_chrome_containers()}
    )


@router.delete("/delete-directory/{random_tag}")
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
