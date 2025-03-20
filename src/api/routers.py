import shutil
import os
import redis
import re
import zipfile
import io
from fastapi import Request, HTTPException, Depends, APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from containers import (
    find_all_chrome_containers,
    find_container_by_tag,
    launch_chrome_container,
    stop_container
)
from fastapi.responses import StreamingResponse
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


@router.delete("/delete/{user_id}")
def delete_container(user_id: str, redis_db: redis.Redis = Depends(get_redis)):
    """Останавливает и удаляет контейнер, связанный с user_id"""
    try:
        if not user_id:
            raise HTTPException(400, "Требуется user_id")

        tag = redis_db.get(f"user:{user_id}")
        if not tag:
            return {"status": "not_found", "message": "Контейнер не найден"}

        container_info = find_container_by_tag(tag)
        if not container_info:
            return {"status": "not_found", "message": "Контейнер не найден"}

        stop_container(container_info)
        redis_db.delete(f"user:{user_id}")

    except Exception as e:
        raise HTTPException(500, f"Ошибка при удалении контейнера: {str(e)}")


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

    dir_path = os.path.join("/root", "downloads", random_tag)

    if not dir_path or not os.path.exists(dir_path):
        raise HTTPException(404, "Директория не найдена")

    try:
        shutil.rmtree(dir_path)
        return {"status": "success", "message": "Директория удалена"}
    except Exception as e:
        raise HTTPException(500, f"Ошибка удаления: {str(e)}")


@router.get("/download-files/{user_id}")
async def download_files(user_id: str, redis_db: redis.Redis = Depends(get_redis)):
    """
    Возвращает все файлы из директории контейнера в виде ZIP-архива
    """
    random_tag = redis_db.get(f"user:{user_id}")
    if not re.match("^[a-zA-Z0-9]{8}$", random_tag):
        raise HTTPException(400, "Некорректный формат тега")

    dir_path = os.path.join("/root", "downloads", random_tag)

    if not os.path.exists(dir_path):
        raise HTTPException(404, "Директория не найдена")

    zip_buffer = io.BytesIO()

    try:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dir_path)
                    zipf.write(file_path, arcname)
    except Exception as e:
        raise HTTPException(500, f"Ошибка создания архива: {str(e)}")

    zip_buffer.seek(0)
    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={random_tag}_files.zip",
            "Content-Length": str(zip_buffer.getbuffer().nbytes)
        }
    )
