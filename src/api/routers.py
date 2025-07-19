import shutil
import os
from pydantic import BaseModel
import redis
import re
import zipfile
import subprocess
from io import BytesIO
from fastapi import Request, HTTPException, Depends, APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from containers.containers import (
    find_all_chrome_containers,
    find_container_by_tag,
    launch_chrome_container,
    stop_container
)
from fastapi.responses import StreamingResponse
from src.core.database import get_redis
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Константа для максимального числа одновременных контейнеров
MAX_CONCURRENT_USERS = 3

class CreateContainerRequest(BaseModel):
    user_id: str = "1"
    website: str = "scopus"


@router.post("/create")
def create_container(request: CreateContainerRequest, redis_db: redis.Redis = Depends(get_redis)):
    """Создает контейнер и связывает его с user_id в Redis"""
    user_id = request.user_id
    website = request.website

    existing_tag = redis_db.get(f"user:{user_id}")
    if existing_tag:
        container_info = find_container_by_tag(existing_tag)
        return {
            "status": "exists",
            "container_info": container_info,
            "access_url": f"https://opensci.ru/access/{user_id}"
        }

    current_containers = find_all_chrome_containers()
    if len(current_containers) >= MAX_CONCURRENT_USERS:
        raise HTTPException(
            status_code=429,
            detail=f"Сервис перегружен. Пожалуйста, попробуйте через 15 минут."
        )

    container_info = launch_chrome_container(website=website)
    tag = container_info["random_tag"]

    redis_db.setex(f"user:{user_id}", 86400, tag)

    return {
        "status": "created",
        "container_info": container_info,
        "access_url": f"https://opensci.ru/access/{user_id}"
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
    target_url = f"http://opensci.ru/vnc/{novnc_port}/vnc.html?autoconnect=true&resize=scale"

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
            redis_db.delete(f"user:{user_id}") # Удаляем запись из Redis, если контейнера уже нет
            return {"status": "not_found", "message": "Контейнер не найден, запись в Redis удалена"}

        stop_container(container_info)
        redis_db.delete(f"user:{user_id}")
        
        return {"status": "success", "message": f"Контейнер для {user_id} удален."}

    except Exception as e:
        logger.error(f"Ошибка при удалении контейнера для {user_id}: {str(e)}")
        raise HTTPException(500, f"Ошибка при удалении контейнера: {str(e)}")


@router.get("/containers")
def list_containers():
    """Возвращает список всех запущенных контейнеров."""
    return find_all_chrome_containers()


@router.delete("/delete-directory/{user_id}")
def delete_directory(user_id: str, redis_db: redis.Redis = Depends(get_redis)):
    """Удаляет директорию контейнера по его тегу."""
    if not user_id:
        raise HTTPException(400, "Требуется user_id")

    random_tag = redis_db.get(f"user:{user_id}")
    if not random_tag:
        return {"status": "not_found", "message": "Контейнер не найден"}
    try:
        random_tag_str = random_tag.decode('utf-8')
    except:
        random_tag_str = random_tag

    dir_path = os.path.join("/root", "Downloads", random_tag_str)

    if not os.path.exists(dir_path):
        raise HTTPException(404, "Директория не найдена")

    try:
        shutil.rmtree(dir_path)
        return {"status": "success", "message": "Директория удалена"}
    except Exception as e:
        logger.error(f"Ошибка удаления директории {dir_path}: {e}")
        raise HTTPException(500, f"Ошибка удаления: {str(e)}")


@router.get("/download-files/{user_id}")
async def download_files(user_id: str, redis_db: redis.Redis = Depends(get_redis)):
    """Возвращает архив файлов пользователя."""
    try:
        random_tag_bytes = redis_db.get(f"user:{user_id}")
        
        if not random_tag_bytes:
            raise HTTPException(status_code=404, detail=f"No files found for user ID: {user_id}")

        try:
            random_tag = random_tag_bytes.decode('utf-8')
        except:
            random_tag = random_tag_bytes

        dir_path = os.path.join("/root", "Downloads", random_tag)

        if not os.path.isdir(dir_path):
            raise HTTPException(status_code=404, detail=f"Directory not found for tag: {random_tag}")

        files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
        
        if not files:
            raise HTTPException(status_code=404, detail="No files found in the directory")

        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                file_path = os.path.join(dir_path, file)
                zip_file.write(file_path, arcname=file)

        zip_buffer.seek(0)

        archive_name = f"opensci_files_{user_id}.zip"

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={archive_name}"}
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error during file download for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/ping")
def ping():
    """Проверяет доступность сервиса."""
    return {"status": "ok"}