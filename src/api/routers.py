import shutil
import os
import redis
import re
import zipfile
import subprocess
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


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
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
        random_tag = redis_db.get(f"user:{user_id}")
        
        if not random_tag:
            logger.error(f"No tag found in Redis for user_id: {user_id}")
            raise HTTPException(status_code=404, detail=f"Тег не найден для ID пользователя: {user_id}")

        dir_path = os.path.join("/root", "downloads", random_tag)
        logger.info(f"Directory path: {dir_path}")

        if not os.path.exists(dir_path):
            logger.error(f"Directory does not exist: {dir_path}")
            raise HTTPException(status_code=404, detail=f"Директория не существует: {dir_path}")

        if not os.path.isdir(dir_path):
            logger.error(f"Path exists but is not a directory: {dir_path}")
            raise HTTPException(status_code=404, detail=f"Путь существует, но не является директорией: {dir_path}")

        logger.info(f"Attempting to list files in: {dir_path}")

        os_listdir_files = os.listdir(dir_path)
        logger.info(f"os.listdir found {len(os_listdir_files)} items: {os_listdir_files}")

        import glob
        glob_files = glob.glob(f"{dir_path}/*")
        logger.info(f"glob found {len(glob_files)} items: {glob_files}")

        try:
            ls_output = subprocess.check_output(['ls', '-la', dir_path], universal_newlines=True)
            logger.info(f"ls -la output:\n{ls_output}")
        except Exception as e:
            logger.error(f"Error running ls command: {str(e)}")

        try:
            dir_stat = os.stat(dir_path)
            logger.info(f"Directory permissions: {oct(dir_stat.st_mode)}")

            import pwd, grp
            try:
                dir_owner = pwd.getpwuid(dir_stat.st_uid).pw_name
                dir_group = grp.getgrgid(dir_stat.st_gid).gr_name
                logger.info(f"Directory owner: {dir_owner}, group: {dir_group}")
            except Exception as e:
                logger.error(f"Error getting owner/group info: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting directory stats: {str(e)}")

        files = [f for f in os_listdir_files if os.path.isfile(os.path.join(dir_path, f))]
        logger.info(f"After filtering, found {len(files)} regular files: {files}")

        for file in files:
            file_path = os.path.join(dir_path, file)
            try:
                file_stat = os.stat(file_path)
                logger.info(f"File '{file}' permissions: {oct(file_stat.st_mode)}")
            except Exception as e:
                logger.error(f"Error getting stats for file '{file}': {str(e)}")
        
        if not files:
            specific_file = os.path.join(dir_path, "new_dump_art.sql")
            if os.path.exists(specific_file):
                logger.info(f"Specific file exists: {specific_file}")
                if os.path.isfile(specific_file):
                    logger.info(f"It is a regular file")
                    files = ["new_dump_art.sql"]
                else:
                    logger.info(f"It exists but is not a regular file")
            else:
                logger.info(f"Specific file does not exist: {specific_file}")
                raise HTTPException(status_code=404, detail=f"В директории нет файлов. Путь: {dir_path}, содержимое: {os_listdir_files}")

        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                file_path = os.path.join(dir_path, file)
                logger.info(f"Adding file to archive: {file_path}")

                try:

                    temp_dir = "/tmp/download_temp"
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_file = os.path.join(temp_dir, file)

                    shutil.copy2(file_path, temp_file)
                    logger.info(f"Successfully copied file to temp location: {temp_file}")

                    zip_file.write(temp_file, arcname=file)
                    logger.info(f"Successfully added file to archive: {file}")

                    os.remove(temp_file)
                except Exception as e:
                    logger.error(f"Failed to add file {file} to archive: {str(e)}")

        zip_buffer.seek(0)

        buffer_size = len(zip_buffer.getvalue())
        logger.info(f"Zip buffer size: {buffer_size} bytes")
        
        if buffer_size == 0:
            logger.error("Zip buffer is empty!")
            raise HTTPException(status_code=500, detail="Ошибка создания архива: архив пуст")

        archive_name = f"files_{user_id}.zip"

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={archive_name}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file download: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Внутренняя ошибка сервера: {str(e)}. Путь директории: {dir_path if dir_path else 'неизвестен'}"
        )