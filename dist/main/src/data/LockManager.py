import threading
import time
from time import  sleep
import time as _time  # Изменяем импорт
from datetime import datetime
import threading
import os
import sys
import logging




class LockManager:
    def __init__(self, lock_file: str):
        self.lock_file = lock_file
        self.running = True
        self.update_interval = 20  # секунд
        self.lock_thread = threading.Thread(target=self.update_lock, daemon=True)

    def start(self):
        """Запустить поток обновления блокировки"""

        self.lock_thread.start()

    def stop(self):
        """Остановить поток обновления блокировки"""

        self.running = False
        if self.lock_thread.is_alive():
            self.lock_thread.join(timeout=1)
        self.cleanup()

    def update_lock(self):
        """Периодически обновлять метку времени в файле блокировки"""

        while self.running:
            try:
                with open(self.lock_file, 'w') as f:
                    timestamp = _time.time()
                    f.write(str(timestamp))

            except Exception as e:
                pass
            _time.sleep(self.update_interval)

    def cleanup(self):
        """Удалить файл блокировки"""
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)

        except Exception as e:
           pass
