# Entry point for КСБ Саундгард.
# MainWindow class lives in src/ui/root/MainWindow.py (Phase 0, Task 2).
import logging
import os
import sys
import traceback
import time as _time  # used in check_lock / main()

import psutil
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QTextEdit

try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    pass  # exec-контекст (напр. PyCharm console) — CWD уже должен быть корнем проекта

import paths

from src.data.LockManager import LockManager
from src.ui.fragments.LoadingScreen import LoadingScreen
from src.utils.logger_config import setup_logger

# Настройка логгера для отладки блокировки
lock_logger = logging.getLogger('lock_manager')
lock_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
lock_logger.addHandler(handler)


def check_lock(lock_file: str) -> bool:
    """Проверить возможность запуска приложения"""
    try:
        if not os.path.exists(lock_file):
            lock_logger.info("Файл блокировки отсутствует, разрешаем запуск")
            return True

        with open(lock_file, 'r') as f:
            content = f.read().strip()

        if not content:
            lock_logger.info("Файл блокировки пуст, разрешаем запуск")
            return True

        last_time = float(content)
        current_time = _time.time()

        lock_logger.info(
            f"Текущее время: {current_time}, время блокировки: {last_time}, разница: {current_time - last_time}")

        # Проверяем свежесть метки (30 секунд - максимальный возраст)
        if (current_time - last_time) > 30:
            lock_logger.info("Метка устарела, разрешаем запуск")
            return True
        else:
            lock_logger.info("Свежая метка блокировки, запрещаем запуск")
            return False
    except Exception as e:
        lock_logger.error(f"Ошибка проверки блокировки: {e}")
        return True


def remove_lock_file(lock_file):
    # Удаляем файл блокировки при завершении приложения
    if os.path.exists(lock_file):
        os.remove(lock_file)

def driver_reload():
    processes = psutil.process_iter()
    for process in processes:
        try:
            # Получаем список открытых файлов процесса
            open_files = process.open_files()
            for file in open_files:
                if '/dev/snd/' in file.path:
                    logger.info(f"\ndriver_reload: Найден процесс с PID {process.pid}, завершение...\n")
                    process.terminate()
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            pass


from src.ui.root.MainWindow import MainWindow

def except_hook(exc_type, exc_value, exc_traceback):
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    error_dialog = QMessageBox()
    error_dialog.setWindowTitle("Ошибка")
    error_dialog.setWindowIcon(QIcon(f"{paths.img_files}{os.sep}logo (2).png"))

    # Создаем QTextEdit и устанавливаем его в качестве пользовательского виджета
    text_edit = QTextEdit()
    text_edit.setText(f"Произошла ошибка:\n{str(error_msg[:-200])}")
    text_edit.setReadOnly(True)  # Сделать его только для чтения
    text_edit.setFixedWidth(250)
    text_edit.setFixedHeight(200)
    error_dialog.layout().addWidget(text_edit)

    logging.error(f"Произошла ошибка:\n{error_msg}")
    print(f"Произошла ошибка:\n{error_msg}")
    error_dialog.exec_()


sys.excepthook = except_hook

logger = setup_logger()

#
def main():
    # Сначала проверяем блокировку до создания QApplication
    lock_file = 'app_lock.txt'

    # Проверка блокировки перед запуском
    if not check_lock(lock_file):
        # Создаем временное приложение для показа сообщения
        temp_app = QApplication(sys.argv)
        QMessageBox.critical(
            None,  # Родительское окно (None - без родителя)
            "Ошибка запуска",
            "Приложение уже запущено!\nПожалуйста, закройте предыдущую копию перед запуском новой.",
            QMessageBox.Ok
        )
        sys.exit(1)

    # Основное приложение
    app = QApplication(sys.argv)

    try:
        # Инициализация GUI
        loading_screen = LoadingScreen()
        loading_screen.show()

        # Создаем файл блокировки
        try:
            with open(lock_file, 'w') as f:
                timestamp = _time.time()
                f.write(str(timestamp))
            lock_logger.info(f"Файл блокировки создан: {timestamp}")
        except Exception as e:
            QMessageBox.critical(
                None,
                "Ошибка запуска",
                f"Не удалось создать файл блокировки:\n{str(e)}",
                QMessageBox.Ok
            )
            sys.exit(1)

        # Даем время для отображения загрузочного экрана
        QApplication.processEvents()

        # Создаем менеджер блокировки
        lock_manager = LockManager(lock_file)

        window = MainWindow(app)
        window.lock_manager = lock_manager  # Сохраняем ссылку на менеджер блокировки
        lock_manager.start()  # Запускаем обновление блокировки

        window.launch_system_checker()
        window.launch_status_connection()

        loading_screen.finish(window)
        window.show()

        return app.exec_()

    finally:
        # Гарантированная очистка блокировки при завершении
        lock_logger.info("Завершение приложения, очистка блокировки")
        if 'lock_manager' in locals():
            lock_manager.stop()
        else:
            # Если не удалось создать окно, все равно очищаем блокировку
            try:
                if os.path.exists(lock_file):
                    os.remove(lock_file)
                    lock_logger.info("Файл блокировки удален в блоке finally")
            except:
                pass


if __name__ == "__main__":
    main()