#!/usr/bin/env python3
"""
Скрипт для сборки Docker образа chrome-vnc-custom.
Запустите этот скрипт для предварительной сборки образа.
"""

import docker
import os
import sys

def build_chrome_image():
    """Собирает Docker образ chrome-vnc-custom."""
    
    client = docker.from_env()
    image_tag = "chrome-vnc-custom"
    
    # Ищем директорию chrome_builder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    build_context_path = os.path.join(current_dir, "chrome_builder")
    
    if not os.path.exists(build_context_path):
        print(f"Ошибка: Директория {build_context_path} не найдена!")
        return False
    
    if not os.path.exists(os.path.join(build_context_path, "Dockerfile")):
        print(f"Ошибка: Dockerfile не найден в {build_context_path}!")
        return False
    
    print(f"Сборка образа {image_tag} из {build_context_path}")
    print("Это может занять несколько минут...")
    
    try:
        # Сборка образа с подробным выводом
        image, build_logs = client.images.build(
            path=build_context_path,
            tag=image_tag,
            rm=True,        # Удалять промежуточные контейнеры
            nocache=False,  # Использовать кэш при возможности
            pull=False      # Не обновлять базовый образ принудительно
        )
        
        # Выводим логи сборки
        for log in build_logs:
            if 'stream' in log:
                print(log['stream'].strip())
        
        print(f"\n✅ Образ {image_tag} успешно собран!")
        print(f"Image ID: {image.id}")
        
        return True
        
    except docker.errors.BuildError as e:
        print(f"❌ Ошибка сборки образа:")
        for log in e.build_log:
            if 'stream' in log:
                print(log['stream'].strip())
        return False
        
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    success = build_chrome_image()
    sys.exit(0 if success else 1)
