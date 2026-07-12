# Рефактор `main.py` → MVVM/Clean — план реализации

> **For agentic workers:** REQUIRED SUB-SKILL: используйте superpowers:subagent-driven-development (рекомендуется) или superpowers:executing-plans для выполнения по одной задаче. Шаги отмечаются чекбоксами (`- [ ]`).

**Goal:** разбить God-object `MainWindow` (1703 стр., ~70 методов в одном классе `main.py`) на слои Application/View/ViewModel/repositories **без изменения поведения**.

**Architecture:** переносим код слоями по образцу Android MVVM: `main.py` = только точка входа (Application); `MainWindow` = тонкая View (рендер + проброс кликов); логика уезжает в фич-ViewModel'ы (`src/viewmodel/`), связь через Qt-сигналы; доступ к данным — в `src/data/repositories/`. Каждый шаг — чистый перенос существующих тел методов, поведение не меняется.

**Tech Stack:** Python 3, PyQt5 (`qtpy`), watchdog, psutil, pyaudio, requests, rtp. Проверка — реальный запуск `python main.py` + skill `qt-testing` (offscreen-снимки). Автотестов в проекте НЕТ.

## Global Constraints

- 🔴 **Fleet-compat (см. `COMPATIBILITY.md`):** НЕ переименовывать и НЕ трогать ключи протокола/MQTT/JSON — `command`, `filename`, `filesize`, `crc`, `value`, `button` и т.п. ~100 клиентов в поле, ломать формат нельзя.
- 🟢 Внутренние имена (классы, методы, локальные переменные) — переименовывать свободно, но переименования делаются **отдельными шагами после** структурного переноса (Фаза 4), не смешиваем с переносом.
- **Перенос без смены поведения:** тело метода переезжает как есть; на шаге переноса допускается только смена `self.` → делегирование, не правка логики.
- **Ветки:** вся работа от `refactor/mainwindow-mvvm`. Каждая задача — свой коммит; merge в `dev` на безопасных чекпойнтах (после Фазы 0, после каждой фичи). `main` не трогаем. См. `WORKFLOW.md`.
- **НЕ трогаем** вёрстку `src/ui/root/UI_MainWindow.py` и wire-протокол. JSON→SQL НЕ делаем (только оформляем репозитории под будущую замену — YAGNI).

### Как проверяется КАЖДАЯ задача (общий блок верификации, автотестов нет)

Везде, где ниже написано «**Верификация**», это значит выполнить все пункты:

1. **Импорт-чек:** `python -c "import main"` — без ошибок импорта (ловит опечатки/циклические импорты до запуска GUI).
2. **Реальный запуск:** `python main.py` — приложение стартует без трейсбека; вручную прощёлкать функцию, которую затронул шаг (см. «Что прощёлкать» в задаче). Cocoa ≠ offscreen — запуск обязателен именно реальный.
3. **qt-testing:** снять offscreen-снимок через skill `qt-testing` в ДВУХ размерах — минимальном `1300×700` И большом (развёрнутое окно); сравнить с эталоном до изменения — картинка идентична.
4. **Diff-ревью:** `git diff` — глазами; свериться с `COMPATIBILITY.md` (не тронуты ли ключи протокола/MQTT/JSON). Только после этого — коммит.

---

## File Structure (целевая)

- `main.py` — **Application**: `main()`, lock-файл, `except_hook`, `setup_logger`, запуск. Класс `MainWindow` отсюда УХОДИТ.
- `src/utils/app_helpers.py` — **создать**: чистые модуль-функции, которые сейчас лежат в `main.py` и используются методами (`convert_seconds`, `sanitize_filename`, `cut_filename`, `last_five_chars_of_datetime_timestamp`, `settings`, `mic_is_ready`). Причина: после выноса `MainWindow` в отдельный файл эти хелперы должны быть импортируемы без циклической зависимости на `main`.
- `src/ui/root/MainWindow.py` — **создать**: класс `MainWindow` (View). Со временем худеет — держит только виджеты, `__init__`-обвязку UI, проброс сигналов в ViewModel, чисто-визуальные методы.
- `src/ui/root/UI_MainWindow.py` — вёрстка (**есть, не трогаем**).
- `src/viewmodel/__init__.py` + фич-ViewModel'ы (**создать по одной за фазу**): `main_viewmodel.py`, `files_viewmodel.py`, `scenarios_viewmodel.py`, `zones_viewmodel.py`, `tts_viewmodel.py`, `recording_viewmodel.py`, `playback_viewmodel.py`.
- `src/data/repositories/` — **создать** (Фаза 3): интерфейсы + JSON-реализации, адаптеры над существующими `ZoneItemRepository`, `FileItemRepository`.

---

## Задачи

### Task 1: Вынести чистые хелперы в `src/utils/app_helpers.py`

Подготовка к выносу класса: развязываем модуль-функции, чтобы будущий `MainWindow.py` не импортировал `main`.

**Files:**
- Create: `src/utils/app_helpers.py`
- Modify: `main.py` (удалить перенесённые функции, добавить импорт)

**Interfaces:**
- Produces: `convert_seconds(seconds) -> str`, `sanitize_filename(text) -> str`, `cut_filename(s) -> str`, `last_five_chars_of_datetime_timestamp() -> str`, `settings() -> dict`, `mic_is_ready() -> bool`. Эти же имена используют методы `MainWindow` (сейчас как модуль-функции) — после переноса они будут импортироваться.

- [ ] **Шаг 1: Проверить всех потребителей хелперов.**
  Выполнить, чтобы знать, где чинить вызовы:
  ```bash
  cd sg_client_2026
  grep -nE "convert_seconds|sanitize_filename|cut_filename|last_five_chars_of_datetime_timestamp|mic_is_ready|(^|[^.])\bsettings\(" main.py
  ```
  Ожидается: вызовы внутри методов `MainWindow` (`settings()` в `__init__`, `sanitize_filename`/`cut_filename` в yandex/файлах, `convert_seconds` в таймере записи и т.д.).

- [ ] **Шаг 2: Создать `src/utils/app_helpers.py`.**
  Перенести ТЕЛА функций `convert_seconds` (main.py:160-165), `sanitize_filename` (168-176), `cut_filename` (179-185), `last_five_chars_of_datetime_timestamp` (154-157), `settings` (188-190), `mic_is_ready` (193-208) как есть. Добавить нужные импорты в новый файл: `import re, json, pyaudio` и `from datetime import datetime`, `import paths`, а также `from src.utils.logger_config import setup_logger; logger = setup_logger()` для `mic_is_ready`/логов (свериться, какой `logger` используется в теле — если это глобальный `logger` из main, завести локальный через `logging.getLogger(__name__)`).

- [ ] **Шаг 3: В `main.py` удалить перенесённые определения** (строки 154-208 диапазона этих 6 функций) и добавить импорт:
  ```python
  from src.utils.app_helpers import (
      convert_seconds, sanitize_filename, cut_filename,
      last_five_chars_of_datetime_timestamp, settings, mic_is_ready,
  )
  ```

- [ ] **Шаг 4: Верификация** (импорт-чек → запуск → qt-testing ×2 → diff). Что прощёлкать: старт приложения (использует `settings()`), запись (таймер зовёт `convert_seconds`), загрузка/озвучка файла (`sanitize_filename`).

- [ ] **Шаг 5: Commit**
  ```bash
  git add src/utils/app_helpers.py main.py
  git commit -m "refactor: вынести чистые хелперы из main.py в src/utils/app_helpers.py"
  ```

---

### Task 2: Вынести класс `MainWindow` в `src/ui/root/MainWindow.py`

Ядро Фазы 0: `main.py` становится точкой входа, класс уезжает в свой файл. Пока это ЧИСТЫЙ перенос — логика внутри класса не меняется.

**Files:**
- Create: `src/ui/root/MainWindow.py`
- Modify: `main.py` (удалить класс, импортировать его)

**Interfaces:**
- Consumes: `app_helpers.*` (Task 1).
- Produces: `class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow)` с конструктором `__init__(self, application)`; используется в `main()` как `MainWindow(app)`.

- [ ] **Шаг 1: Создать `src/ui/root/MainWindow.py`.** Перенести целиком тело `class MainWindow` (main.py:211-1604, включая все методы вплоть до `perform_cleanup_actions`). Перенести в новый файл ВСЕ импорты, которые использует класс (скопировать блок import из main.py:3-70 и убрать неиспользуемые после проверки). Добавить `from src.utils.app_helpers import convert_seconds, sanitize_filename, cut_filename, last_five_chars_of_datetime_timestamp, settings, mic_is_ready` и `from src.utils.logger_config import setup_logger; logger = setup_logger()` (класс использует глобальный `logger`).

- [ ] **Шаг 2: В `main.py` удалить тело класса** и добавить `from src.ui.root.MainWindow import MainWindow`. В `main.py` оставить: import-блок для точки входа, `check_lock`/`remove_lock_file`/`driver_reload`/`set_light_theme`/`set_dark_theme` (модуль-функции темы — их использует `init_menu_bar`; см. Шаг 3), `except_hook`, `sys.excepthook`/`logger`, `main()`, `if __name__`.

- [ ] **Шаг 3: Развязать модуль-функции темы.** `MainWindow.init_menu_bar` (1060-1080) цепляет `QAction` на модуль-функции `set_light_theme`/`set_dark_theme` (main.py:138-151). Проверить: `grep -n "set_light_theme\|set_dark_theme" main.py src/ui/root/MainWindow.py`. Эти две функции перенести в `src/utils/app_helpers.py` (пишут `theme` в `paths.settings`) и импортировать в `MainWindow.py`. ВНИМАНИЕ: в классе тоже есть методы `set_light_theme`/`set_dark_theme` (1052-1059) — это РАЗНЫЕ вещи (методы применяют тему к UI), их НЕ трогаем, только модуль-функции разводим. Коллизию имён (метод vs функция) фиксируем в Фазе 4.

- [ ] **Шаг 4: Верификация** (импорт-чек → запуск → qt-testing ×2 → diff). Что прощёлкать: полный старт, переключение вкладок, смена темы через меню (light/dark), закрытие окна (cleanup).

- [ ] **Шаг 5: Commit**
  ```bash
  git add src/ui/root/MainWindow.py src/utils/app_helpers.py main.py
  git commit -m "refactor(phase0): вынести класс MainWindow в src/ui/root/MainWindow.py, main.py — точка входа"
  ```

- [ ] **Шаг 6: Чекпойнт-merge Фазы 0 в `dev`** (после ревью diff). По `WORKFLOW.md`: `git switch dev && git merge --no-ff refactor/mainwindow-mvvm`, затем вернуться на ветку рефактора. (Или PR, если так принято — свериться с WORKFLOW.)

---

### Task 3: Каркас `MainViewModel` (Фаза 1)

Пустой агрегатор, подключённый к окну. Логику пока НЕ переносим — только создаём слой и связь View↔ViewModel, чтобы следующие фичи было куда переносить.

**Files:**
- Create: `src/viewmodel/__init__.py` (пустой), `src/viewmodel/main_viewmodel.py`
- Modify: `src/ui/root/MainWindow.py` (создать VM в `__init__`)

**Interfaces:**
- Produces: `class MainViewModel(QObject)` c конструктором `__init__(self, view)` (хранит ссылку на View для сигналов на первом этапе) и точками расширения-атрибутами под фич-VM (заполнятся в Фазе 2). `MainWindow.vm: MainViewModel`.

- [ ] **Шаг 1: Создать `src/viewmodel/main_viewmodel.py`:**
  ```python
  from PyQt5.QtCore import QObject


  class MainViewModel(QObject):
      """Агрегатор фич-ViewModel'ей. Заполняется по мере переноса фич (Фаза 2)."""

      def __init__(self, view):
          super().__init__()
          self.view = view
          # фич-VM подключаются здесь в Фазе 2:
          # self.files = FilesViewModel(view)
          # self.zones = ZonesViewModel(view)
          # ...
  ```

- [ ] **Шаг 2: В `MainWindow.__init__`** (после `setupUi`, ближе к концу конструктора, до `self.show`-логики в main) создать VM: `self.vm = MainViewModel(self)`. Импорт: `from src.viewmodel.main_viewmodel import MainViewModel`.

- [ ] **Шаг 3: Верификация** (импорт-чек → запуск → qt-testing ×2 → diff). Поведение не меняется — приложение стартует как раньше.

- [ ] **Шаг 4: Commit**
  ```bash
  git add src/viewmodel/__init__.py src/viewmodel/main_viewmodel.py src/ui/root/MainWindow.py
  git commit -m "refactor(phase1): каркас MainViewModel, подключён к MainWindow"
  ```

---

### Фаза 2 — рецепт переноса одной фичи (применяется к задачам 4-9)

Все фич-задачи идентичны по процессу. Для каждой фичи:

1. **Создать** `src/viewmodel/<feature>_viewmodel.py` с `class <Feature>ViewModel(QObject)`, `__init__(self, view)` (хранит `self.view`, при необходимости — репозитории/воркеры, которые сейчас создаёт `MainWindow.__init__`).
2. **Перенести тела** перечисленных методов из `MainWindow` в VM как есть. Внутри VM обращения к виджетам временно идут через `self.view.<widget>` (View пока владеет виджетами) — это осознанный промежуточный шаг, вылизывание связности не входит в перенос.
3. **Перенести владение состоянием**: атрибуты `MainWindow.__init__`, относящиеся к фиче (список ниже per-task), переезжают в `<Feature>ViewModel.__init__`; в местах чтения/записи из других мест — через VM.
4. **Перецепить сигналы**: в `MainWindow.__init__` строки `self.<widget>.<signal>.connect(self.<method>)` для методов фичи заменить на `...connect(self.vm.<feature>.<method>)`. В `MainViewModel.__init__` добавить `self.<feature> = <Feature>ViewModel(view)`.
5. **Оставить в View тонкую делегацию** там, где метод дёргается из другого слоя по имени (`self.method(...)` → `self.vm.<feature>.method(...)`), чтобы не сломать внешних вызывающих на этом шаге.
6. **Верификация** (общий блок) — прощёлкать именно эту фичу. **Commit.** Порядок фич: от простого/оффлайнового к сетевому.

🔴 На всех шагах — не трогать ключи протокола/MQTT/JSON (Global Constraints).

---

### Task 4: FilesViewModel (Фаза 2 — фича «Файлы»)

Самая изолированная фича (локальные файлы, сортировка, поиск) — начинаем с неё.

**Files:** Create `src/viewmodel/files_viewmodel.py`; Modify `src/ui/root/MainWindow.py`, `src/viewmodel/main_viewmodel.py`.

**Методы к переносу** (`MainWindow` → `FilesViewModel`): `update_file_list` (1225), `sort_by_name` (1235), `sort_by_date` (1243), `on_search_changed` (1254), `play_file_local` (1262), `delete_file` (1277), `rename_file` (1284), `add_description_to_file_item` (1294), `add_file_item` (1303), `upload_custom_file` (1324), `get_file_item_file_name` (1355), `update_list_on_slider` (1218).

**Состояние → VM:** `self.files_repo` (298), `self.FILE_LIST` (300), `self.sort_key` (244), `self.name_reverse_key` (245), `self.date_reverse_key` (246), `self.grid_size` (310).

**Сигналы к перецепке** (`MainWindow.__init__`): `sort_by_name_btn`(268), `sort_by_date_btn`(269), `search_input`(270), `upload_custom_file_btn`(271), `list_scale_slider`(276), `file_list_widget.delete_clicked`(281), `.listen_clicked`(282), `.rename_clicked`(283), `.add_description_clicked`(284).

- [ ] Шаг 1: Создать `files_viewmodel.py`, перенести методы (рецепт п.1-2).
- [ ] Шаг 2: Перенести состояние (рецепт п.3). Учесть: `grid_size`/`update_list_on_slider` также трогает `apply_theme` (1556) и `__init__` (313) — оставить в View тонкую делегацию `self.update_list_on_slider = self.vm.files.update_list_on_slider` или заменить вызовы на `self.vm.files....`.
- [ ] Шаг 3: Перецепить сигналы + `self.files = FilesViewModel(view)` в `MainViewModel` (рецепт п.4).
- [ ] Шаг 4: View-делегация для внешних вызовов `update_file_list`/`add_file_item` (их зовёт yandex-поток, Task 7) — оставить прокси-методы (рецепт п.5).
- [ ] Шаг 5: **Верификация** — прощёлкать: список файлов, сортировка по имени/дате, поиск, воспроизведение локально, удаление/переименование/описание, загрузка своего файла, слайдер масштаба списка.
- [ ] Шаг 6: Commit `refactor(phase2): FilesViewModel — перенос логики файлов из MainWindow`.

---

### Task 5: ScenariosViewModel (Фаза 2 — фича «Сценарии»)

**Files:** Create `src/viewmodel/scenarios_viewmodel.py`; Modify `MainWindow.py`, `main_viewmodel.py`.

**Методы к переносу:** `load_scenarios` (385), `on_task_executed` (363), `on_modified` (349).

**Состояние → VM:** `self.sheduler`/`Scheduler` (326-327), `self.event_handler`/`self.observer` (330-333), связанные с планировщиком объекты. ВНИМАНИЕ: `Scheduler(paths.shedule_data_scenaries, self.on_task_executed)` — колбэк теперь `self.vm.scenarios.on_task_executed`.

**Сигналы/колбэки:** конструктор `Scheduler`/`FileChangeHandler` в `__init__` (326-333).

- [ ] Шаг 1: Создать VM, перенести 3 метода.
- [ ] Шаг 2: Перенести создание `Scheduler`/`Observer` в VM (или оставить в View, но колбэк указывать на VM) — выбрать минимально-инвазивный вариант, зафиксировать в diff.
- [ ] Шаг 3: `self.scenarios = ScenariosViewModel(view)` в агрегаторе.
- [ ] Шаг 4: **Верификация** — прощёлкать: список сценариев грузится; сработавший по расписанию сценарий отрабатывает (`on_task_executed`); правка файла сценариев подхватывается (`on_modified`).
- [ ] Шаг 5: Commit `refactor(phase2): ScenariosViewModel`.

---

### Task 6: ZonesViewModel (Фаза 2 — фича «Зоны», сетевая)

**Files:** Create `src/viewmodel/zones_viewmodel.py`; Modify `MainWindow.py`, `main_viewmodel.py`.

**Методы к переносу:** `auto_search_zones` (1105), `rename_zone` (1125), `add_zone_from_file` (1140), `add_zone` (1147), `remove_zone` (1170), `update_zones` (1182), `update_zone_status` (1195), `update_ui` (1207), `orange_status_receiver` (1214), `update_online_status` (483), `update_statuses` (489), `on_connected` (501), `launch_status_connection` (474), `launch_system_checker` (470).

**Состояние → VM:** `self.zones_repo` (297), `self.ZONE_LIST` (301), `self.layout_manager` (231), `self.status_api` (303-304), `self.connection_thread` (306-307), `self.system_checker` (314-317).

**Сигналы к перецепке:** `zone_add_btn`(262), `auto_search_zones_btn`(264), `zone_refresh_btn`(265), `zone_list_widget.rename_clicked`(286), `.delete_clicked`(287), `status_api.status_changed`(304), `connection_thread.connected`(307). ВАЖНО: `main()` зовёт `window.launch_system_checker()` и `window.launch_status_connection()` (1680-1681) — оставить в View прокси-методы, делегирующие в `self.vm.zones`, чтобы `main()` не менять.

- [ ] Шаг 1: Создать VM, перенести методы.
- [ ] Шаг 2: Перенести состояние; `status_api.status_changed.connect(self.vm.zones.orange_status_receiver)`.
- [ ] Шаг 3: View-прокси `launch_system_checker`/`launch_status_connection` для `main()`.
- [ ] Шаг 4: `self.zones = ZonesViewModel(view)` в агрегаторе.
- [ ] Шаг 5: **Верификация** — прощёлкать: автопоиск зон, добавить/переименовать/удалить зону, статусы онлайн/оффлайн обновляются, обновление по кнопке refresh. 🔴 убедиться, что MQTT-топики/ключи не тронуты.
- [ ] Шаг 6: Commit `refactor(phase2): ZonesViewModel`.

---

### Task 7: TtsViewModel (Фаза 2 — фича «Озвучка/Yandex»)

**Files:** Create `src/viewmodel/tts_viewmodel.py`; Modify `MainWindow.py`, `main_viewmodel.py`.

**Методы к переносу:** `launch_yandex_process` (516), `yandex_things` (1416), `on_ya_response` (1370), `select_voice_menu` (1012), `set_voice_params` (1027), `get_voice_params` (1031), `progress_update` (1365), `on_ffmpeg_finished` (1486).

**Состояние → VM:** `self.selected_voice` (253), объекты `YandexThread`/`FfmpegThread` (создаются внутри методов).

**Сигналы к перецепке:** `text_to_file_btn`(261), `voice_select_btn`(277). Учесть: `yandex_things` зовётся из `__init__` (346) при первом запуске (загрузка шаблонов) и из `TtsViewModel`; и вызывает `add_file_item`/`update_file_list` (Task 4) — идёт через `self.view.vm.files....`.

- [ ] Шаг 1: Создать VM, перенести методы.
- [ ] Шаг 2: Перенести `selected_voice`; связать межфичевые вызовы к `files` через агрегатор.
- [ ] Шаг 3: Перецепить сигналы + `self.tts = TtsViewModel(view)`; в `__init__`-блоке загрузки шаблонов (336-347) заменить `self.yandex_things(data)` → `self.vm.tts.yandex_things(data)`.
- [ ] Шаг 4: **Верификация** — прощёлкать: выбор голоса, синтез текста в файл (Yandex→ffmpeg), прогресс-бар, появление файла в списке. 🔴 не трогать ключи запроса к Yandex API.
- [ ] Шаг 5: Commit `refactor(phase2): TtsViewModel`.

---

### Task 8: RecordingViewModel (Фаза 2 — фича «Запись»)

**Files:** Create `src/viewmodel/recording_viewmodel.py`; Modify `MainWindow.py`, `main_viewmodel.py`.

**Методы к переносу:** `launch_rec` (545), `do_rec` (885), `start_recording` (914), `stop_recording` (936), `on_new_audio_chunk` (895), `update_record_timer` (930), `handle_recognizer_result` (958), `handle_empty_recognition` (988), `handle_no_microphone` (1086).

**Состояние → VM:** `self.recorder` (249), `self.timer_for_record` (250-251), `self.indication`/`self.indication_mic` (247-248), `self.waveform_viewer` (289), `self.start_time` (215).

**Сигналы к перецепке:** `record_btn`(273), `timer_for_record.timeout`(251), `mic_usage_indicator` (295 — visibility).

- [ ] Шаг 1: Создать VM, перенести методы.
- [ ] Шаг 2: Перенести состояние (recorder/timer/waveform). `timer_for_record.timeout.connect(self.vm.recording.update_record_timer)`.
- [ ] Шаг 3: `self.recording = RecordingViewModel(view)`.
- [ ] Шаг 4: **Верификация** — прощёлкать: старт/стоп записи, таймер, индикатор микрофона, распознавание результата, ветки «пусто»/«нет микрофона». Проверить и при отсутствии микрофона (`handle_no_microphone`).
- [ ] Шаг 5: Commit `refactor(phase2): RecordingViewModel`.

---

### Task 9: PlaybackViewModel (Фаза 2 — фича «Воспроизведение/Orange», самая сетевая — последняя)

**Files:** Create `src/viewmodel/playback_viewmodel.py`; Modify `MainWindow.py`, `main_viewmodel.py`.

**Методы к переносу:** `commit_orange_command` (559), `commit_orange_command_scenario` (635), `launch_play` (530), `launch_stop` (553), `launch_realtime` (523), `orange_realtime` (811), `start_rtp_session` (823), `handle_streamer_message` (843), `handle_stream_status` (849), `on_streaming_status_changed` (707), `on_thread_finished` (715), `on_orange_finished` (997), `on_orange_success` (1002), `send_new_volume_value` (513), `tcp_orange_callback_status` (1461), `indicate_file_played_on_orange` (1478), `handle_some_msg` (1472), `handle_alarm_off` (1465). **Дубли** (перенести оба, развести в Фазе 4): `orange_stop` (793 и 801), `orange_stop_realtime` (855 и 864).

**Состояние → VM:** `self.play_threads`/`stop_threads`/`realtime_play_threads`/`stop_realtime_threads` (234-237), `self.success_IPs` (238), `self.finished_threads` (239), `self.is_streaming_flag` (243), `self.audio_streamer` (254), `self.status_sender` (255-257).

**Сигналы к перецепке:** `play_btn`(259), `stop_btn`(260), `realtime_button`(278), `stop_realtime_button`(279), `update_volume_on_oranges_btn`(275), `volume_slider`(274 → `set_volume`; проверить, где определён `set_volume`, его тоже перенести/оставить как View-делегат). Учесть: `perform_cleanup_actions` (1567) обращается к `play_threads`/`is_streaming_flag`/`orange_stop_realtime` — после переноса читать через `self.vm.playback....`.

- [ ] Шаг 1: Создать VM, перенести методы (включая оба дубля — НЕ чинить сейчас).
- [ ] Шаг 2: Перенести состояние потоков/стриминга; обновить `perform_cleanup_actions` на доступ через VM.
- [ ] Шаг 3: Перецепить сигналы + `self.playback = PlaybackViewModel(view)`.
- [ ] Шаг 4: **Верификация** — прощёлкать: play/stop на зонах, realtime старт/стоп, изменение громкости, реакция на статусы Orange по TCP, закрытие окна (cleanup терминирует потоки). 🔴 команды/ключи протокола Orange НЕ трогать.
- [ ] Шаг 5: Commit `refactor(phase2): PlaybackViewModel`.
- [ ] Шаг 6: **Чекпойнт-merge Фазы 2 в `dev`** после ревью.

---

### Task 10: Data-слой — репозитории (Фаза 3)

Оформить интерфейс + JSON-реализацию, чтобы позже можно было заменить на SQL. JSON→SQL сейчас НЕ делаем (YAGNI).

**Files:** Create `src/data/repositories/__init__.py`, `src/data/repositories/interfaces.py`; Modify — адаптеры над `src/operations_with_zones/ZoneItemRepository.py`, `src/operations_with_files/FileItemRepository.py` (или тонкие обёртки, БЕЗ смены формата файлов).

**Interfaces:**
- Produces: `class IZoneRepository` (методы, которые реально зовёт `ZonesViewModel`: `all_zones`/`get`/`add`/`remove`/сохранение — свериться по факту вызовов), `class IFileRepository` (методы, которые зовёт `FilesViewModel`). Существующие классы объявляются реализациями интерфейса.

- [ ] Шаг 1: `grep` по VM'ам — какие методы репозиториев реально используются:
  ```bash
  grep -nE "zones_repo\.|files_repo\." src/viewmodel/*.py
  ```
- [ ] Шаг 2: Создать `interfaces.py` с ABC-интерфейсами ровно под используемые методы (не шире — YAGNI).
- [ ] Шаг 3: Пометить `ZoneItemRepository`/`FileItemRepository` как реализации (наследование от интерфейса ИЛИ регистрация), не меняя их поведения и формата JSON. 🟡 ключи JSON — только через migrate-on-load, но здесь ключи НЕ трогаем вовсе.
- [ ] Шаг 4: **Верификация** — прощёлкать функции файлов и зон (данные читаются/пишутся как раньше; JSON-файлы на диске бинарно-совместимы — сравнить до/после).
- [ ] Шаг 5: Commit `refactor(phase3): интерфейсы репозиториев (data-слой), JSON-реализации без смены формата`.

---

### Task 11: Чистка — дубли и непонятные имена (Фаза 4)

Только ПОСЛЕ структурного переноса. Отдельные мелкие шаги, каждый — со своей верификацией.

**Известные дефекты:**
- Дубль `orange_stop` — `main.py` 793 и 801 (Python берёт последнее; первое — мёртвый код).
- Дубль `orange_stop_realtime` — 855 и 864.
- Дубль `closeEvent` — 375 и 1563 (второе побеждает; проверить, какое реально нужно).
- Коллизия имён темы: модуль-функции `set_light_theme`/`set_dark_theme` (пишут в settings) vs одноимённые методы класса (1052/1059, применяют к UI) — переименовать одну пару для ясности.

- [ ] Шаг 1: Для каждого дубля — определить, какое определение живое (последнее в исходном классе), удалить мёртвое. По одному дублю за коммит.
- [ ] Шаг 2: `git diff` показать, что удалён именно неиспользуемый (тела дублей могут отличаться — сверить оба перед удалением; если отличаются, это потенциальный баг — вынести владельцу решение).
- [ ] Шаг 3: Переименовать непонятные имена (🟢 внутренние — свободно; ключи протокола/MQTT/JSON — 🔴 НЕ трогать). Примеры-кандидаты: `sheduler`→`scheduler` (атрибут), `things`/`test`/`handle_some_msg` — по согласованию.
- [ ] Шаг 4: **Верификация** после каждого удаления/переименования (запуск + qt-testing + прощёлкать затронутое).
- [ ] Шаг 5: Commit per-fix (`refactor(phase4): убрать дубль orange_stop` и т.п.).
- [ ] Шаг 6: **Финальный чекпойнт-merge в `dev`** + обновить `brain/progress.md` и память `[[ksb-ui-redesign-workstream]]`.

---

## Self-Review (проверка плана против спеки)

- **Покрытие фаз спеки:** Фаза 0 → Task 1-2; Фаза 1 → Task 3; Фаза 2 (6 фич) → Task 4-9; Фаза 3 → Task 10; Фаза 4 → Task 11. ✅ все фазы покрыты.
- **Карта методов спеки:** все группы (Files/Scenarios/Zones/Tts/Recording/Playback + «остаётся в View») распределены по задачам 4-9; методы, помеченные в спеке «остаётся в View» (`__init__`, `set_light_theme`/`set_dark_theme`-методы, `init_menu_bar`, `showSettingsDialog`, `on_tab_changed`, `change_enabled_of_spin_box`, `update_progress_bar`, `dragEnterEvent`, `dropEvent`, `closeEvent`, `test`, `apply_theme`, `perform_cleanup_actions`) — НЕ переносятся, остаются в `MainWindow`. ✅
- **Дубли:** `orange_stop`/`orange_stop_realtime` из спеки + дополнительно найденные `closeEvent` и коллизия темы — в Task 11. ✅
- **Ограничения:** fleet-compat/протокол, «перенос без смены поведения», ветки, проверка запуском+qt-testing — в Global Constraints и в каждом блоке верификации. ✅
- **Отличие от шаблона skill'а:** TDD-шаги заменены реальной верификацией (запуск + qt-testing + diff), т.к. автотестов в проекте нет — это соответствует спеке. Осознанное решение, не placeholder.
