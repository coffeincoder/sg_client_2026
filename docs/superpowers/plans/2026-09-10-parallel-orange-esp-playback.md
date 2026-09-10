# Параллельное воспроизведение Orange+ESP32 (режим file/scenario) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Дать серверу режим воспроизведения (`mode` в команде `play`): `file` — Orange на все линии; `scenario` — Orange на линии 1–4 + ESP32 на 5–8 параллельно (2 файла). UI сценариев — 8 combo-box со связкой по группам.

**Architecture:** Клиент (PyQt5, MVVM) в команду `play` кладёт `mode`. Сервер по `mode` ставит коммутатор (`Analog_in_commutator`). ESP-файл в сценарии уходит существующими командами `load_esp`/`play_esp` (контракт ii). Логика выбора коммутатора — чистая функция, тестируется без железа.

**Tech Stack:** Python 3, PyQt5, встроенный `unittest`, скилл `qt-testing` (offscreen-скриншоты). Клиент — репо `sg_client_2026`; сервер — репо `sg_orange_2026-`.

**Spec:** `sg_client_2026/docs/superpowers/specs/2026-09-10-parallel-orange-esp-playback-design.md`

## Global Constraints

- **Совместимость флота (~100 клиентов):** нет `mode` в команде → сервер трактует `'file'`. НЕ переименовывать существующие ключи протокола/JSON; только добавлять.
- **Формат данных сценария не меняем:** 8 combo-box пишут в существующие 2 поля `file` (группа 1–4) и `file_esp` (группа 5–8).
- **Без эмодзи в UI** (UI для пожилых дежурных; крупные контролы) — правила `ksb-client-ui-design-rules`.
- **Железо отложено:** реальный параллельный звук проверяется на Orange позже. Локально сервер не запускается (нет GPIO/serial) — серверные задачи проверяем юнит-тестом чистой логики + `py_compile`, не запуском.
- **Прогон тестов клиента:** `.venv/bin/python -m unittest discover -s tests -v` из корня `sg_client_2026`.
- **Прогон тестов сервера:** `python3 -m unittest discover -s tests -v` из корня `sg_orange_2026-`.
- **Коммиты** заканчивать строкой `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

---

## Task 0: Коммит плана

**Files:** Commit: `docs/superpowers/plans/2026-09-10-parallel-orange-esp-playback.md`

Ветка `feature/parallel-orange-esp` (клиент) уже создана от `feature/zone-8-channels`, спек закоммичен (97d0da6).

- [ ] **Step 1: Закоммитить план**

```bash
cd sg_client_2026
git add docs/superpowers/plans/2026-09-10-parallel-orange-esp-playback.md
git commit -m "docs: план параллельного воспроизведения Orange+ESP32"
```

---

## Task 1: [СЕРВЕР] resolve_source_mode — чистая логика выбора коммутатора

**Repo:** `sg_orange_2026-` (ветку под серверную часть завести ОТДЕЛЬНО, координируясь с sun0 — см. Task 6 примечание; здесь — только новый самостоятельный модуль, конфликтов не создаёт).

**Files:**
- Create: `source_mode.py`
- Test: `tests/test_source_mode.py`

**Interfaces:**
- Produces: `resolve_source_mode(mode) -> str` — имя метода коммутатора: `'orange_to_both_channel'` для `file`/дефолт, `'orange_to_channel1_esp_to_channel2'` для `scenario`.

- [ ] **Step 1: Написать падающий тест**

```python
# tests/test_source_mode.py
import unittest
from source_mode import resolve_source_mode


class TestResolveSourceMode(unittest.TestCase):
    def test_file(self):
        self.assertEqual(resolve_source_mode("file"), "orange_to_both_channel")

    def test_scenario(self):
        self.assertEqual(resolve_source_mode("scenario"), "orange_to_channel1_esp_to_channel2")

    def test_default_when_absent(self):
        self.assertEqual(resolve_source_mode(None), "orange_to_both_channel")

    def test_default_when_unknown(self):
        self.assertEqual(resolve_source_mode("garbage"), "orange_to_both_channel")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Прогнать — FAIL** (`python3 -m unittest tests.test_source_mode -v` → нет модуля `source_mode`).

- [ ] **Step 3: Реализовать модуль**

```python
# source_mode.py
"""Выбор режима источника звука (коммутатора) по режиму воспроизведения.
file     -> Orange на оба аудио-канала (orange_to_both_channel)
scenario -> Orange на 1-й, ESP32 на 2-й (orange_to_channel1_esp_to_channel2)
Неизвестное/None -> file (совместимость со старыми клиентами)."""

_MODES = {
    "file": "orange_to_both_channel",
    "scenario": "orange_to_channel1_esp_to_channel2",
}


def resolve_source_mode(mode):
    return _MODES.get(mode, "orange_to_both_channel")
```

- [ ] **Step 4: Прогнать — PASS** (`python3 -m unittest tests.test_source_mode -v`).

- [ ] **Step 5: Commit**

```bash
git add source_mode.py tests/test_source_mode.py
git commit -m "feat(server): resolve_source_mode — коммутатор по режиму play (file/scenario)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: [СЕРВЕР] Прокинуть mode в play + поставить коммутатор

**Repo:** `sg_orange_2026-`

**Files:**
- Modify: `ServerState.py` (метод `play`, + импорт)
- Modify: `sg_main.py` (обработчик `data["command"]=="play"`)

**Interfaces:**
- Consumes: `resolve_source_mode` (Task 1).
- Produces: `ServerState.play(self, loop, filename, mode='file')` — в начале ставит коммутатор `getattr(self.com, resolve_source_mode(mode))()`.

- [ ] **Step 1: Импорт в ServerState.py**

Рядом с `from src.python3.esp.Analog_in_commutator import *` (строка ~26) добавить:
```python
from source_mode import resolve_source_mode
```

- [ ] **Step 2: Сигнатура play + установка коммутатора**

В `def play(self, loop, filename):` изменить сигнатуру на `def play(self, loop, filename, mode='file'):` и ПЕРВОЙ строкой тела (до печатей `active`) добавить:
```python
        getattr(self.com, resolve_source_mode(mode))()
```
(Так `file`/дефолт → `orange_to_both_channel()`, `scenario` → `orange_to_channel1_esp_to_channel2()`.)

- [ ] **Step 3: Читать mode в sg_main.py и прокинуть в поток**

В обработчике `elif data["command"] == "play":` (перед созданием `playing_thread`) добавить:
```python
            mode = data.get("mode", "file")
```
и изменить создание потока на:
```python
            playing_thread = threading.Thread(target=server_state.play,
                                              args=(server_state.loop, file_path_to_wav, mode))
```

- [ ] **Step 4: Проверка синтаксиса (без запуска — нет железа)**

Run: `python3 -m py_compile ServerState.py sg_main.py source_mode.py` → без ошибок.
Run: `python3 -m unittest discover -s tests -v` → все тесты (вкл. Task 1) PASS.
Примечание: реальный запуск play на Orange — отложенный железный тест.

- [ ] **Step 5: Commit**

```bash
git add ServerState.py sg_main.py
git commit -m "feat(server): play читает mode и ставит коммутатор (file/scenario), дефолт file

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: [КЛИЕНТ] mode в команде play (build_play_command + параметр воркера)

**Repo:** `sg_client_2026`

**Files:**
- Modify: `src/network/OrangeWorkerTCP.py`
- Test: `tests/test_build_play_command.py`

**Interfaces:**
- Produces: `build_play_command(filename, mode='file') -> dict` (`{"command":"play","filename":...,"mode":...}`); `OrangeWorkerTCP.__init__(..., mode='file')` со `self.mode`.

- [ ] **Step 1: Написать падающий тест**

```python
# tests/test_build_play_command.py
import unittest
from src.network.OrangeWorkerTCP import build_play_command


class TestBuildPlayCommand(unittest.TestCase):
    def test_default_mode_is_file(self):
        self.assertEqual(
            build_play_command("a.wav"),
            {"command": "play", "filename": "a.wav", "mode": "file"},
        )

    def test_scenario_mode(self):
        self.assertEqual(
            build_play_command("a.wav", "scenario"),
            {"command": "play", "filename": "a.wav", "mode": "scenario"},
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Прогнать — FAIL** (`.venv/bin/python -m unittest tests.test_build_play_command -v` — нет `build_play_command`).

- [ ] **Step 3: Реализовать функцию + параметр воркера**

В `OrangeWorkerTCP.py` на уровне модуля (рядом с другими функциями, до класса) добавить:
```python
def build_play_command(filename, mode='file'):
    """Команда play с режимом воспроизведения (mode: 'file' | 'scenario')."""
    return {"command": "play", "filename": filename, "mode": mode}
```
В `__init__` (строка 72) добавить параметр `mode='file'` (в конец списка) и в теле: `self.mode = mode`.
На строке ~135 заменить инлайн-словарь:
```python
                    response = send_command(client_socket,
                                            build_play_command(os.path.basename(self.file_path), self.mode),
                                            ip)
```

- [ ] **Step 4: Прогнать — PASS** (`.venv/bin/python -m unittest tests.test_build_play_command -v`).

- [ ] **Step 5: Тест параметра воркера + весь набор**

Добавить в `tests/test_build_play_command.py`:
```python
    def test_worker_stores_mode(self):
        from src.network.OrangeWorkerTCP import OrangeWorkerTCP
        w = OrangeWorkerTCP(command="play", ip="1.1.1.1", text="", mode="scenario")
        self.assertEqual(w.mode, "scenario")

    def test_worker_default_mode(self):
        from src.network.OrangeWorkerTCP import OrangeWorkerTCP
        w = OrangeWorkerTCP(command="play", ip="1.1.1.1", text="")
        self.assertEqual(w.mode, "file")
```
Run: `.venv/bin/python -m unittest discover -s tests -v` → PASS.

- [ ] **Step 6: Commit**

```bash
git add src/network/OrangeWorkerTCP.py tests/test_build_play_command.py
git commit -m "feat(client): mode в команде play (build_play_command + параметр воркера)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: [КЛИЕНТ] Прокинуть mode из путей воспроизведения

**Repo:** `sg_client_2026`

**Files:**
- Modify: `src/viewmodel/playback_viewmodel.py` (`commit_orange_command`, `commit_orange_command_scenario`)
- Modify: `src/ui/root/MainWindow.py` (`orange_play`, `orange_play_scenario`)

**Interfaces:**
- Consumes: `OrangeWorkerTCP(..., mode=...)` (Task 3).
- Produces: `commit_orange_command(..., mode='file')` и `commit_orange_command_scenario(..., mode='scenario')` передают `mode` в воркер.

- [ ] **Step 1: Параметр mode в commit_orange_command**

В `playback_viewmodel.commit_orange_command` добавить в сигнатуру `mode='file'` и при создании `OrangeWorkerTCP(...)` добавить аргумент `mode=mode`.

- [ ] **Step 2: Параметр mode в commit_orange_command_scenario**

Аналогично в `commit_orange_command_scenario` добавить `mode='scenario'` в сигнатуру и `mode=mode` в `OrangeWorkerTCP(...)`.

- [ ] **Step 3: Прокинуть из MainWindow**

В `MainWindow.orange_play` вызов `self.commit_orange_command(command="play", ...)` дополнить `mode='file'`.
В `MainWindow.orange_play_scenario` вызов `self.commit_orange_command_scenario(command="play", ...)` дополнить `mode='scenario'`.

- [ ] **Step 4: Прогон**

Run: `.venv/bin/python -m unittest discover -s tests -v` → все PASS (регрессий нет; тесты воркера из Task 3 подтверждают проброс).

- [ ] **Step 5: Commit**

```bash
git add src/viewmodel/playback_viewmodel.py src/ui/root/MainWindow.py
git commit -m "feat(client): прокинуть mode (file/scenario) из путей воспроизведения в воркер

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: [КЛИЕНТ] Сценарий досылает ESP-файл (load_esp/play_esp)

**Repo:** `sg_client_2026`

**Files:**
- Modify: `src/viewmodel/playback_viewmodel.py` (`commit_orange_command_scenario`)
- Test: `tests/test_scenario_esp_dispatch.py`

**Interfaces:**
- Produces: в сценарии для каждой зоны, если ESP-файл (`file_esp`) непустой, дополнительно создаётся `OrangeWorkerTCP(command='play_esp', ip=..., file_path=<esp>, loop=..., text='')`.

**Важно (сверить перед кодом):** прочитать, как `commit_orange_command_scenario` (строки ~183-200) получает элементы сценария и есть ли у элемента поле ESP-файла. `ScenarioItemModel` имеет `file` и `file_esp`; убедиться, что в SEND-пути доступен `file_esp` (при необходимости адаптировать чтение элемента). Пустой `file_esp` → ESP не шлём.

- [ ] **Step 1: Тест guard-функции**

Вынести решение «слать ли ESP» в чистую функцию в `playback_viewmodel.py`:
```python
# tests/test_scenario_esp_dispatch.py
import unittest
from src.viewmodel.playback_viewmodel import should_send_esp


class TestShouldSendEsp(unittest.TestCase):
    def test_empty_no(self):
        self.assertFalse(should_send_esp(""))
        self.assertFalse(should_send_esp(None))

    def test_nonempty_yes(self):
        self.assertTrue(should_send_esp("evac.mp3"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Прогнать — FAIL** (нет `should_send_esp`).

- [ ] **Step 3: Реализовать guard**

В `playback_viewmodel.py` (уровень модуля):
```python
def should_send_esp(file_esp):
    """Слать ли ESP-файл в сценарии: только при непустом имени."""
    return bool(file_esp and str(file_esp).strip())
```

- [ ] **Step 4: Досылка ESP в цикле сценария**

В `commit_orange_command_scenario`, внутри цикла по элементам сценария, после создания Orange-воркера, добавить (имя ESP-файла берётся из элемента сценария — `item.file_esp` или эквивалент, сверенный в примечании выше):
```python
                esp_name = getattr(item, "file_esp", "") or ""
                if should_send_esp(esp_name):
                    esp_worker = OrangeWorkerTCP(
                        command='play_esp',
                        ip=str(item.zone.ip),
                        text=text,
                        loop=loop,
                        file_path=os.path.join(paths.mp3_files, esp_name),
                        vol=vol,
                        overload_value=overload_value,
                    )
                    thread_list.append(esp_worker)
```
(ESP-файл поедет по существующему пути `load_esp`/`play_esp` внутри воркера при `command='play_esp'`.)

- [ ] **Step 5: Прогон**

Run: `.venv/bin/python -m unittest discover -s tests -v` → PASS.

- [ ] **Step 6: Commit**

```bash
git add src/viewmodel/playback_viewmodel.py tests/test_scenario_esp_dispatch.py
git commit -m "feat(client): сценарий досылает ESP-файл через play_esp (контракт ii)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: [КЛИЕНТ UI] 8 combo-box сценария со связкой по группам

**Repo:** `sg_client_2026`

**Files:**
- Modify: `src/ui/fragments/ZoneLayoutManager.py` (построение строки зоны + `save_scen`/`load_scen`)

**Interfaces:**
- Produces: на каждую зону — 8 `QComboBox`, сгруппированы 1–4 (Orange) и 5–8 (ESP32); связка по группе (выбор в любом боксе группы заполняет все её боксы); сохранение — группа 1–4 → `file`, группа 5–8 → `file_esp`.

**Текущее состояние:** строки ~401-419 создают 2 бокса (`combox_chan1`, `combox_chan2`) на зону; `save_scen`/`load_scen` (~78-116) читают/пишут `combox_main`(idx1)/`combox_esp`(idx2). Заменяем на 8 боксов с группами.

- [ ] **Step 1: Построить 8 боксов с группировкой и автозаполнением**

В блоке построения строки зоны заменить создание двух боксов на цикл из 8. Для каждой группы связать боксы: изменение любого бокса группы ставит его текст во все боксы группы (защита от рекурсии флагом). Хранить боксы, напр., в `row_combos = {1..8: QComboBox}` и добавить в `self.main_window.scen_layouts` структуру, из которой `save_scen` возьмёт представителя группы. Подписи столбцов/групп: «Orange (линии 1–4)» и «ESP32 (линии 5–8)». Каждый бокс: `addItems([""] + headers)`, стиль `self.setup_combobox_style(...)`, без эмодзи.

Пример связки по группе (для группы боксов `group = [cb1..cb4]`):
```python
        def _bind_group(group):
            def make_handler(src):
                def on_changed(_idx):
                    if getattr(self, "_autofill_guard", False):
                        return
                    self._autofill_guard = True
                    try:
                        text = src.currentText()
                        for cb in group:
                            if cb is not src:
                                cb.setCurrentText(text)
                    finally:
                        self._autofill_guard = False
                return on_changed
            for cb in group:
                cb.currentIndexChanged.connect(make_handler(cb))
```

- [ ] **Step 2: save_scen — группы → file / file_esp**

В `save_scen` брать текст представителя каждой группы: `file` = текст любого бокса группы 1–4, `file_esp` = текст любого бокса группы 5–8 (внутри группы они равны из-за связки). Формат `ScenarioItemModel(zone, file, file_esp)` не менять.

- [ ] **Step 3: load_scen — file → все 1–4, file_esp → все 5–8**

В `load_scen` при восстановлении: `saved_item.file` поставить во все боксы группы 1–4, `saved_item.file_esp` — во все 5–8 (через `setCurrentText`).

- [ ] **Step 4: Скриншот через qt-testing**

Отрендерить вкладку сценариев (или её область) с несколькими зонами: проверить 8 боксов на зону, две видимые группы (1–4 / 5–8) с подписями, что выбор в одном боксе группы заполняет остальные боксы этой группы, вертикально/по сетке не разъезжается на мин. и большом окне. (См. скилл `qt-testing`.)

- [ ] **Step 5: Прогон тестов**

Run: `.venv/bin/python -m unittest discover -s tests -v` → PASS (существующие не сломаны).

- [ ] **Step 6: Commit**

```bash
git add src/ui/fragments/ZoneLayoutManager.py
git commit -m "feat(client): 8 combo-box сценария со связкой по группам (Orange 1-4 / ESP32 5-8)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

- **Покрытие спека:** §3 флаг mode (T2 сервер читает, T3/T4 клиент шлёт), §4 контракт ii ESP через play_esp (T5), §5 клиентские правки протокола (T3/T4/T5), §5.1 8 combo-box + автозаполнение (T6), §6 сервер mode→коммутатор (T1/T2), §7 совместимость (T1 дефолт file, формат данных неизменен), §9 проверки (юнит-тесты T1/T3/T5, qt-testing T6, железо отложено). Все разделы покрыты.
- **Совместимость:** нет mode → `resolve_source_mode(None)` = `orange_to_both_channel` (T1), `data.get("mode","file")` (T2), `build_play_command` дефолт `file` (T3). ✓
- **Типы/имена:** `resolve_source_mode` (T1)→T2; `build_play_command`/`OrangeWorkerTCP.mode` (T3)→T4; `should_send_esp` (T5). Согласованы.
- **Данные:** формат сценария (`file`/`file_esp`) не меняется (T5/T6). ✓
- **Риск (T5):** SEND-путь сценария может использовать иную обёртку элемента, чем `ScenarioItemModel` — примечание в T5 требует сверки перед кодом.
- **Координация sun0 (серверные T1/T2):** отдельная ветка в `sg_orange_2026-`, `git pull` перед правкой, предупредить (урок отката парсера). Сообщение Диме — после готовности кода.
