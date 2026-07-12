# Рефактор `main.py` → MVVM / Clean — дизайн

**Дата:** 2026-07-12
**Ветка работы:** `refactor/mainwindow-mvvm` (от `dev`)
**Статус:** дизайн утверждён владельцем, готов к написанию плана.

## Цель

Разбить «God object» `MainWindow` (1703 строки, 83 метода) на слои по образцу
Android MVVM / Clean Architecture: отделить логику от UI, сделать файлы обозримыми,
почистить непонятные имена и дубли — **без изменения поведения** (fleet-критичный код,
~100 клиентов в поле, автотестов нет).

## Текущее состояние (боль)

`src/ui/root/UI_MainWindow.py` — вёрстка (ок, не трогаем). Вся логика — в `main.py`,
класс `MainWindow(QMainWindow, Ui_MainWindow)`: 83 метода, в одном классе перемешаны
UI-события, сеть/Orange, аудио-запись, озвучка, зоны, файлы, планировщик, тема.
Известные дефекты: дубли-методы `orange_stop` (стр. 793/801) и `orange_stop_realtime`
(855/864) — Python молча берёт последнее определение.

## Целевая архитектура (маппинг Android → PyQt)

| Android | У нас | Роль |
|---------|-------|------|
| `Application` | `main.py` | точка входа: `main()`, lock-файл, `QApplication` |
| `MainActivity` | `MainWindow` (`src/ui/root/MainWindow.py`) | **View**: рендер + проброс кликов, подписан на сигналы ViewModel |
| `MainViewModel` | слой `src/viewmodel/` | **логика и состояние**, отделены от окна |
| Repositories + impl | слой `src/data/repositories/` | доступ к данным (JSON сейчас, SQL — задел на потом) |

**Связь MVVM:** ViewModel держит состояние и шлёт Qt-сигналы → View перерисовывается;
клики из View вызывают методы ViewModel. View не содержит бизнес-логики; ViewModel не
знает про конкретные виджеты.

## Структура файлов (целевая)

```
main.py                          # Application — только запуск
src/ui/root/
  UI_MainWindow.py               # вёрстка (есть, не трогаем)
  MainWindow.py                  # View (тонкое окно)
src/viewmodel/
  main_viewmodel.py              # MainViewModel — агрегатор фич-виюмоделей
  zones_viewmodel.py             # ZonesViewModel
  playback_viewmodel.py          # PlaybackViewModel  (Orange-команды/воспроизведение)
  recording_viewmodel.py         # RecordingViewModel (аудио-запись)
  tts_viewmodel.py               # TtsViewModel       (озвучка/Yandex)
  files_viewmodel.py             # FilesViewModel
  scenarios_viewmodel.py         # ScenariosViewModel
src/data/repositories/           # часть уже есть (ZoneItemRepository, FileItemRepository)
  ...                            # оформить интерфейсы + реализации
```

## Карта методов → ViewModel (для плана)

Приблизительная группировка 83 методов (уточнить при переносе):

- **FilesViewModel:** `update_file_list`, `sort_by_name`, `sort_by_date`, `on_search_changed`,
  `play_file_local`, `delete_file`, `rename_file`, `add_description_to_file_item`,
  `add_file_item`, `upload_custom_file`, `get_file_item_file_name`, `update_list_on_slider`.
- **ScenariosViewModel:** `load_scenarios`, `on_task_executed`, `on_modified`.
- **ZonesViewModel:** `auto_search_zones`, `rename_zone`, `add_zone`, `add_zone_from_file`,
  `remove_zone`, `update_zones`, `update_zone_status`, `orange_status_receiver`,
  `update_online_status`, `update_statuses`, `on_connected`, `launch_status_connection`,
  `launch_system_checker`, `update_ui`.
- **TtsViewModel:** `launch_yandex_process`, `yandex_things`, `on_ya_response`,
  `select_voice_menu`, `set_voice_params`, `get_voice_params`, `progress_update`,
  `on_ffmpeg_finished`.
- **RecordingViewModel:** `launch_rec`, `do_rec`, `start_recording`, `stop_recording`,
  `on_new_audio_chunk`, `update_record_timer`, `handle_recognizer_result`,
  `handle_empty_recognition`, `handle_no_microphone`.
- **PlaybackViewModel:** `commit_orange_command`, `commit_orange_command_scenario`,
  `launch_play`, `launch_stop`, `launch_realtime`, `orange_stop`, `orange_realtime`,
  `orange_stop_realtime`, `start_rtp_session`, `handle_streamer_message`,
  `handle_stream_status`, `on_streaming_status_changed`, `on_thread_finished`,
  `on_orange_finished`, `on_orange_success`, `send_new_volume_value`,
  `tcp_orange_callback_status`, `indicate_file_played_on_orange`, `handle_some_msg`,
  `handle_alarm_off`.
- **Остаётся в View (`MainWindow`):** `__init__`, `setupUi`-обвязка, `set_light_theme`,
  `set_dark_theme`, `init_menu_bar`, `showSettingsDialog`, `on_tab_changed`,
  `change_enabled_of_spin_box`, `update_progress_bar`, `dragEnterEvent`, `dropEvent`,
  `closeEvent`, `test`.

## Порядок работ (фазы)

Каждая фаза — по одной фиче за раз, своя под-ветка/коммит, проверка запуском + qt-testing,
merge в `dev` на безопасных чекпойнтах.

0. **`main.py` → точка входа.** Вынести `main()`/lock/loading, оставить только запуск.
1. **Каркас `MainViewModel`** — пустой агрегатор, подключён к окну.
2. **Фичи по одной** (от простого к сетевому): файлы → сценарии → зоны → TTS → запись →
   воспроизведение. Каждая: перенести логику из окна в свою ViewModel, провести сигналы,
   проверить, смержить.
3. **Data-слой** — оформить репозитории (интерфейсы + JSON-реализация).
4. **Чистка** — фикс дублей (`orange_stop`, `orange_stop_realtime`) и переименование
   непонятных имён (отдельными шагами, после структурного переноса).

## Безопасность и ограничения

- **Перенос без смены поведения** — на каждом шаге логика переезжает как есть.
- 🔴 **Fleet-compat:** НЕ трогать ключи протокола/MQTT/JSON (`command/filename/filesize/
  crc/value/button/…`). Внутренние имена методов/переменных — свободно (🟢). См.
  `COMPATIBILITY.md`.
- **Проверка каждого шага:** `python main.py` (реальный запуск, cocoa ≠ offscreen) + скилл
  `qt-testing` (мин 1300×700 и большое окно) + просмотр diff перед merge (`WORKFLOW.md`).
- **Ветки:** вся работа от `refactor/mainwindow-mvvm`; шаги — под-ветки/коммиты, merge в
  `dev` на чекпойнтах. `main` не трогаем.

## Вне области (YAGNI)

- НЕ делаем JSON→SQL сейчас — только оформляем репозитории так, чтобы реализацию можно
  было заменить позже.
- НЕ трогаем вёрстку `UI_MainWindow.py` и wire-протокол.
- НЕ вводим DI-фреймворки/интерфейсные абстракции сверх необходимого — простые классы.
