import shutil
import os
import redis
import re
import zipfile
from io import BytesIO
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
import logging


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
    try:
        random_tag = redis_db.get(user_id)
        
        if not random_tag:
            raise HTTPException(status_code=404, detail=f"No tag found for user ID: {user_id}")
        
        # Формируем путь к директории с файлами
        dir_path = os.path.join("/root", "downloads", random_tag)
        
        # Проверяем существование директории
        if not os.path.exists(dir_path):
            raise HTTPException(status_code=404, 
                              detail=f"Directory not found: {dir_path}")
        
        # Логируем, что директория найдена и её путь
        logging.info(f"Looking for files in directory: {dir_path}")
        
        # Получаем список файлов в директории
        files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
        
        # Логируем найденные файлы
        logging.info(f"Files found: {files}")
        
        if not files:
            raise HTTPException(status_code=404, 
                              detail=f"В директории нет файлов. Путь директории: {dir_path}")
        
        # Создаем временный буфер для архива
        zip_buffer = BytesIO()
        
        # Создаем архив и добавляем в него файлы
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                file_path = os.path.join(dir_path, file)
                # Проверяем читаемость файла перед добавлением
                try:
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    zip_file.writestr(file, file_content)
                    logging.info(f"Added file to archive: {file}")
                except Exception as e:
                    logging.error(f"Failed to add file {file} to archive: {str(e)}")
        
        # Перемещаем указатель буфера в начало
        zip_buffer.seek(0)
        
        # Создаем имя архива для скачивания
        archive_name = f"files_{user_id}.zip"
        
        # Возвращаем архив как StreamingResponse
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={archive_name}"}
        )
    
    except Exception as e:
        logging.error(f"Error during file download: {str(e)}")
        raise HTTPException(status_code=500, 
                          detail=f"Internal server error: {str(e)}. Dir path: {dir_path if 'dir_path' in locals() else 'unknown'}")