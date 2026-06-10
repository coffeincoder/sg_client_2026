import os
import sys
import time
import atexit
import threading
import hashlib
from pathlib import Path


class SingleInstance:
    def __init__(self, lock_name=".app.lock", ttl_seconds=30):
        # Генерируем уникальное имя для блокировки
        app_path = os.path.abspath(sys.argv[0])
        self.lock_id = hashlib.md5(app_path.encode()).hexdigest()

        if sys.platform == "win32":
            self.lock_file = Path(os.environ.get("TEMP", ".")) / f"{lock_name}.{self.lock_id}"
        else:
            self.lock_file = Path("/tmp") / f"{lock_name}.{self.lock_id}"

        self.ttl = ttl_seconds
        self._lock_handle = None
        self._running = False
        self._updater_thread = None

    def is_running(self):
        """Проверяет, запущен ли уже процесс."""
        try:
            if sys.platform == "win32":
                return self._windows_check()
            else:
                return self._unix_check()
        except Exception as e:
            print(f"Lock error: {e}", file=sys.stderr)
            return False

    def _windows_check(self):
        """Реализация для Windows через мьютекс."""
        try:
            import win32event
            import win32api
            import winerror

            mutex_name = f"Global\\{self.lock_id}"
            self._lock_handle = win32event.CreateMutex(None, False, mutex_name)
            if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                return True
            atexit.register(self._cleanup)
            return False
        except ImportError:
            # Fallback для Windows без pywin32
            return self._file_based_check()

    def _unix_check(self):
        """Реализация для Unix систем."""
        try:
            # Попробуем использовать flock (более надежно чем fcntl)
            self._lock_handle = os.open(self.lock_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)

            import fcntl
            try:
                fcntl.flock(self._lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (BlockingIOError, PermissionError):
                # Проверим, не устарел ли lock
                if self._is_lock_expired():
                    self._force_release()
                    return self._unix_check()
                return True

            self._write_pid()
            atexit.register(self._cleanup)
            self._start_updater()
            return False

        except Exception as e:
            print(f"Unix lock error: {e}", file=sys.stderr)
            return self._file_based_check()

    def _file_based_check(self):
        """Файловая проверка как запасной вариант."""
        try:
            if self._is_lock_expired():
                self._force_release()

            if os.path.exists(self.lock_file):
                with open(self.lock_file, 'r') as f:
                    pid = f.read().strip()
                    if pid and self._is_pid_running(pid):
                        return True

            self._write_pid()
            atexit.register(self._cleanup)
            self._start_updater()
            return False

        except Exception as e:
            print(f"File lock error: {e}", file=sys.stderr)
            return False

    def _write_pid(self):
        """Записываем PID в lock-файл."""
        with open(self.lock_file, 'w') as f:
            f.write(str(os.getpid()))

    def _is_pid_running(self, pid):
        """Проверяет, работает ли процесс с указанным PID."""
        try:
            pid = int(pid)
            if sys.platform == "win32":
                import psutil
                return psutil.pid_exists(pid)
            else:
                os.kill(pid, 0)
                return True
        except:
            return False

    def _is_lock_expired(self):
        """Проверяет, устарел ли lock-файл."""
        try:
            return (time.time() - os.path.getmtime(self.lock_file)) > self.ttl
        except:
            return True

    def _force_release(self):
        """Принудительно освобождает lock."""
        try:
            if self._lock_handle:
                if sys.platform != "win32":
                    import fcntl
                    fcntl.flock(self._lock_handle, fcntl.LOCK_UN)
                os.close(self._lock_handle)
            if os.path.exists(self.lock_file):
                os.unlink(self.lock_file)
        except:
            pass

    def _start_updater(self):
        """Обновляет время lock-файла."""

        def updater():
            while self._running:
                try:
                    os.utime(self.lock_file, None)
                    time.sleep(self.ttl // 2)
                except:
                    break

        self._running = True
        self._updater_thread = threading.Thread(target=updater, daemon=True)
        self._updater_thread.start()

    def _cleanup(self):
        """Очистка ресурсов."""
        self._running = False
        if self._updater_thread:
            self._updater_thread.join(timeout=1)
        self._force_release()
        try:
            atexit.unregister(self._cleanup)
        except:
            pass

    def __del__(self):
        self._cleanup()