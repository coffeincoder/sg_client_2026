# 8 каналов (двухуровневая модель) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Развить каналы с 4 до 8 и перейти на двухуровневую модель: окно задаёт, какие каналы есть у устройства (present) + имена; панель галочками выбирает активные для вещания (active).

**Architecture:** Клиент (PyQt5, MVVM), данные в `zones.json` (dataclass `Orange`). На канал два флага: `subzoneN_present` (есть у устройства) и `subzoneN` (активен). Панель показывает только present-каналы интерактивными галочками (active). Playback шлёт строку активных линий `"1,5,7"` (1..8). Серверная маршрутизация/ESP32 — вне этого плана (sun0), кроме расширения нашего `parse_play_variant` до 1..8.

**Tech Stack:** Python 3.12, PyQt5, встроенный `unittest`, скилл `qt-testing` для окон. Сервер (Task 8): Python 3, репо `sg_orange_2026-`.

**Spec:** `docs/superpowers/specs/2026-08-25-zone-8-channels-design.md`

## Global Constraints

- **Совместимость флота:** НЕ переименовывать существующие ключи `subzone1/subzone2/subzone1_name/subzone2_name` (и `subzone3/4`). Новые поля только добавлять с дефолтами через `.get(...)`.
- **Два флага на канал:** `subzoneN` = active (панель), `subzoneN_present` = есть у устройства (окно).
- **UI-подпись:** «Канал 1»…«Канал 8». Расположение каналов **вертикальное** и в окне, и в панели.
- **Формат протокола:** строка активных линий через запятую, до 8: `"1,5,7"`, `""` = ни одной. НЕ массив.
- **Дефолты:** новый present-канал → active=True; минимум 1 present у устройства; имена сохраняются; активный выбор запоминается.
- **Миграция:** старый `zones.json` → `subzone1_present=True`, `subzone2_present=True`, `subzone3..8_present=False`.
- **Без эмодзи** в коде (UI для пожилых дежурных).
- **Прогон тестов:** `.venv/bin/python -m unittest discover -s tests -v` из корня `sg_client_2026`.

---

## Task 0: Коммит плана

**Files:**
- Commit: `docs/superpowers/plans/2026-08-25-zone-8-channels.md`

- [ ] **Step 1: Закоммитить план** (ветка `feature/zone-8-channels` уже создана, спек уже закоммичен)

```bash
cd sg_client_2026
git add docs/superpowers/plans/2026-08-25-zone-8-channels.md
git commit -m "docs: план 8 каналов (двухуровневая модель)"
```

---

## Task 1: Данные — subzone5..8 + present + миграция

**Files:**
- Modify: `src/data/ZoneModel.py`
- Modify: `src/operations_with_zones/ZoneItemRepository.py`
- Test: `tests/test_zone_model_8ch.py`

**Interfaces:**
- Produces: `Orange` получает `subzone5..8: bool=False`, `subzone5..8_name: str=""`, `subzone1..8_present: bool` (в dataclass дефолт `False`). Репозиторий при загрузке ставит `subzone1_present`/`subzone2_present` в `True`, если ключа нет в файле.

- [ ] **Step 1: Написать падающий тест**

```python
# tests/test_zone_model_8ch.py
import unittest
from src.data.ZoneModel import Orange


class TestZoneModel8ch(unittest.TestCase):
    def test_new_channels_default(self):
        z = Orange()
        for n in (5, 6, 7, 8):
            self.assertEqual(getattr(z, f"subzone{n}"), False)
            self.assertEqual(getattr(z, f"subzone{n}_name"), "")
        for n in range(1, 9):
            self.assertEqual(getattr(z, f"subzone{n}_present"), False)

    def test_present_fields_serialized(self):
        z = Orange(subzone5=True, subzone5_name="эвакуация", subzone5_present=True)
        d = z.to_json()
        self.assertTrue(d["subzone5"])
        self.assertTrue(d["subzone5_present"])
        self.assertEqual(d["subzone5_name"], "эвакуация")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Прогнать — убедиться, что падает**

Run: `.venv/bin/python -m unittest tests.test_zone_model_8ch -v`
Expected: FAIL — нет атрибутов `subzone5` / `subzone1_present`.

- [ ] **Step 3: Добавить поля в dataclass**

В `src/data/ZoneModel.py`, в блоке полей `Orange`, дополнить (существующие 1..4 не трогаем, только добавляем):

```python
    subzone5: bool = False
    subzone6: bool = False
    subzone7: bool = False
    subzone8: bool = False
    subzone5_name: str = ""
    subzone6_name: str = ""
    subzone7_name: str = ""
    subzone8_name: str = ""
    subzone1_present: bool = False
    subzone2_present: bool = False
    subzone3_present: bool = False
    subzone4_present: bool = False
    subzone5_present: bool = False
    subzone6_present: bool = False
    subzone7_present: bool = False
    subzone8_present: bool = False
```

- [ ] **Step 4: Читать новые поля в репозитории (миграция)**

В `src/operations_with_zones/ZoneItemRepository.py`, в КАЖДОМ месте, где строится `Orange(...)` из `zone_data` (их несколько — `init_load` и `add_zone_from_file`), добавить чтение новых полей. Для `active` и имён каналов 5..8 — дефолт как у 3/4. Для `present` — каналы 1 и 2 по умолчанию `True` (старые устройства их имели), остальные `False`:

```python
                subzone5=zone_data.get("subzone5", False),
                subzone6=zone_data.get("subzone6", False),
                subzone7=zone_data.get("subzone7", False),
                subzone8=zone_data.get("subzone8", False),
                subzone5_name=zone_data.get("subzone5_name", ""),
                subzone6_name=zone_data.get("subzone6_name", ""),
                subzone7_name=zone_data.get("subzone7_name", ""),
                subzone8_name=zone_data.get("subzone8_name", ""),
                subzone1_present=zone_data.get("subzone1_present", True),
                subzone2_present=zone_data.get("subzone2_present", True),
                subzone3_present=zone_data.get("subzone3_present", False),
                subzone4_present=zone_data.get("subzone4_present", False),
                subzone5_present=zone_data.get("subzone5_present", False),
                subzone6_present=zone_data.get("subzone6_present", False),
                subzone7_present=zone_data.get("subzone7_present", False),
                subzone8_present=zone_data.get("subzone8_present", False),
```

- [ ] **Step 5: Тест миграции present-дефолтов**

Добавить в `tests/test_zone_model_8ch.py` тест, что старый словарь (без `_present`) через путь репозитория даёт `subzone1_present=True`, `subzone2_present=True`, `subzone3_present=False`. Если поднять репозиторий на temp-файле сложно — проверить логику дефолтов напрямую тем же выражением `.get(...)`. Отметить выбранный способ.

- [ ] **Step 6: Прогнать — PASS**

Run: `.venv/bin/python -m unittest tests.test_zone_model_8ch -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/data/ZoneModel.py src/operations_with_zones/ZoneItemRepository.py tests/test_zone_model_8ch.py
git commit -m "feat(data): каналы 5-8 + subzone_present + миграция present"
```

---

## Task 2: active_channels учитывает present, диапазон 1..8

**Files:**
- Modify: `src/viewmodel/channel_utils.py`
- Test: `tests/test_channel_utils_8ch.py`

**Interfaces:**
- Consumes: `Orange` с `subzone1..8` (active) и `subzone1..8_present`.
- Produces: `active_channels(zone)` возвращает `[n for n in 1..8 if subzoneN and subzoneN_present]`. `format_play_variant` без изменений.

- [ ] **Step 1: Написать падающий тест**

```python
# tests/test_channel_utils_8ch.py
import unittest
from src.data.ZoneModel import Orange
from src.viewmodel.channel_utils import active_channels, format_play_variant


class TestChannelUtils8ch(unittest.TestCase):
    def test_active_requires_present_and_active(self):
        z = Orange(
            subzone1=True, subzone1_present=True,     # активен и есть → входит
            subzone5=True, subzone5_present=False,    # активен, но не present → НЕ входит
            subzone7=True, subzone7_present=True,     # входит
            subzone8=False, subzone8_present=True,    # present, но не активен → нет
        )
        self.assertEqual(active_channels(z), [1, 7])

    def test_format_up_to_8(self):
        self.assertEqual(format_play_variant([1, 5, 7]), "1,5,7")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Прогнать — FAIL** (сейчас `active_channels` идёт 1..4 и не смотрит на present)

Run: `.venv/bin/python -m unittest tests.test_channel_utils_8ch -v`
Expected: FAIL.

- [ ] **Step 3: Обновить active_channels**

В `src/viewmodel/channel_utils.py`:

```python
def active_channels(zone) -> list:
    """Номера каналов, которые есть у устройства (present) И активны (1..8)."""
    return [n for n in range(1, 9)
            if getattr(zone, f"subzone{n}") and getattr(zone, f"subzone{n}_present")]
```

(`format_play_variant` не меняется.)

- [ ] **Step 4: Прогнать всё — PASS**

Run: `.venv/bin/python -m unittest discover -s tests -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/viewmodel/channel_utils.py tests/test_channel_utils_8ch.py
git commit -m "feat(viewmodel): active_channels = present AND active, диапазон 1..8"
```

---

## Task 3: Окно — 8 каналов вертикально (present + имя)

**Files:**
- Modify: `src/ui/fragments/UI_AddZoneWindow.py`

**Interfaces:**
- Consumes: конструктор получает `channels` — список из 8 кортежей `(present: bool, name: str)`.
- Produces:
  - `UI_AddZoneWindow(zone_name, ip, all_zones, channels=None, for_rename=False)`, `channels` по умолчанию 8×`(False, "")`.
  - `get_channels() -> list[tuple[bool, str]]` — 8 пар `(present, name)` в порядке 1..8.

- [ ] **Step 1: Переписать окно на 8 каналов**

В `UI_AddZoneWindow`: цикл `for i in range(8)`, каждая строка — `QCheckBox(f"Канал {i+1}")` (= present) + `QLineEdit` (имя). Чекбокс через `toggled` гасит/включает поле. Расположение вертикальное (каждый канал — своя строка грида, row = `2 + i`). Обновить `get_channels()` на 8 пар. `channels[i]` при `None` → `(False, "")`.

```python
        self.channel_checks = []
        self.channel_fields = []
        for i in range(8):
            chk = QCheckBox(f"Канал {i + 1}")
            fld = QLineEdit()
            fld.setPlaceholderText(f"Введите имя канала {i + 1}")
            present, name = channels[i] if channels else (False, "")
            chk.setChecked(present)
            fld.setText(name)
            fld.setEnabled(present)
            chk.toggled.connect(fld.setEnabled)
            row = 2 + i
            self.input_layout.addWidget(chk, row, 0)
            self.input_layout.addWidget(fld, row, 1)
            self.channel_checks.append(chk)
            self.channel_fields.append(fld)

    def get_channels(self):
        return [(c.isChecked(), f.text()) for c, f in zip(self.channel_checks, self.channel_fields)]
```

Удалить прежний код на 4 канала (поля/циклы 4-канальной версии), геттеры каналов оставить только `get_channels()`.

- [ ] **Step 2: Обновить offscreen-тест окна**

Обновить `tests/test_add_zone_window.py`: конструировать с 8 парами, проверить 8 чекбоксов + 8 полей, что снятая галочка гасит поле, `get_channels()` возвращает 8 пар. Прогнать весь набор.

Run: `.venv/bin/python -m unittest discover -s tests -v` → PASS.

- [ ] **Step 3: Скриншот через qt-testing**

Отрендерить окно с, напр., `channels=[(True,"улица"),(True,"2 этаж"),(False,""),(False,""),(True,"склад"),(False,""),(False,""),(False,"")]`. Проверить: 8 строк вертикально, галочка гасит поле, окно не разъезжается на мин. и большом размере.

- [ ] **Step 4: Commit**

```bash
git add src/ui/fragments/UI_AddZoneWindow.py tests/test_add_zone_window.py
git commit -m "feat(ui): окно зоны на 8 каналов вертикально (present + имя)"
```

---

## Task 4: Сохранение present + правило active (create/rename)

**Files:**
- Modify: `src/viewmodel/zones_viewmodel.py`
- Modify: `src/operations_with_zones/ZoneItemRepository.py` (update_zone_state)
- Test: `tests/test_zone_save_8ch.py`

**Interfaces:**
- Consumes: `UI_AddZoneWindow.get_channels()` — 8 пар `(present, name)`.
- Produces: при создании/редактировании в `Orange` и `zones.json` пишутся `subzone1..8_present`, `subzone1..8_name`, и `subzone1..8` (active) по правилу.

**Правило active при сохранении окна (на канал n):**
- стал present (создание или впервые отметили) → `active = True`;
- был present и остаётся → `active` не менять;
- перестал быть present → `active = False`.

- [ ] **Step 1: Тест правила active (чистая функция-помощник)**

Вынести правило в чистую функцию (проще тестировать), напр. в `channel_utils.py`:

```python
# tests/test_zone_save_8ch.py
import unittest
from src.viewmodel.channel_utils import resolve_active


class TestResolveActive(unittest.TestCase):
    def test_new_present_becomes_active(self):
        # (was_present, is_present, was_active) -> active
        self.assertTrue(resolve_active(False, True, False))   # впервые отметили
    def test_existing_present_keeps_active(self):
        self.assertFalse(resolve_active(True, True, False))   # был present, active как был
        self.assertTrue(resolve_active(True, True, True))
    def test_unpresent_clears_active(self):
        self.assertFalse(resolve_active(True, False, True))   # сняли present


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Прогнать — FAIL** (нет `resolve_active`)

Run: `.venv/bin/python -m unittest tests.test_zone_save_8ch -v`
Expected: FAIL.

- [ ] **Step 3: Реализовать resolve_active**

В `src/viewmodel/channel_utils.py`:

```python
def resolve_active(was_present: bool, is_present: bool, was_active: bool) -> bool:
    """Правило active при сохранении окна устройства."""
    if not is_present:
        return False
    if not was_present:      # канал впервые стал present
        return True
    return was_active        # был present — активность не трогаем
```

- [ ] **Step 4: Расширить update_zone_state**

В `ZoneItemRepository.update_zone_state` добавить параметры `subzone5..8`, `subzone5..8_name`, `subzone1..8_present` (все `Optional=None`), присваивать под `if ... is not None`, как для 1..4.

- [ ] **Step 5: Прокинуть в add_zone**

В `zones_viewmodel.add_zone`: после `Accepted` взять `channels = addZoneDialog.get_channels()`; для нового устройства `was_present=False`, `was_active=False`; собрать `Orange` с `subzoneN_present = channels[n-1][0]`, `subzoneN_name = channels[n-1][1]`, `subzoneN = resolve_active(False, present, False)` (т.е. present → active). Использовать цикл по 1..8, не 8 строк вручную.

- [ ] **Step 6: Прокинуть в rename_zone**

В `zones_viewmodel.rename_zone`: передать в окно текущие `(present, name)` по 8 каналам; после `Accepted` для каждого канала `n`:
```python
    ch = addZoneDialog.get_channels()
    for n in range(1, 9):
        was_present = getattr(zone, f"subzone{n}_present")
        was_active = getattr(zone, f"subzone{n}")
        is_present, name = ch[n - 1]
        setattr(zone, f"subzone{n}_present", is_present)
        setattr(zone, f"subzone{n}_name", name)
        setattr(zone, f"subzone{n}", resolve_active(was_present, is_present, was_active))
```
Затем `self.view.zones_repo.save(...)`.

- [ ] **Step 7: Проверка вручную + прогон**

Run: `.venv/bin/python -m unittest discover -s tests -v` → PASS. Затем запустить `main.py`, создать устройство с каналами 1 и 5, проверить в `zones.json`: `subzone1_present=true`, `subzone5_present=true`, `subzone1=true`, `subzone5=true`, остальные present=false.

- [ ] **Step 8: Commit**

```bash
git add src/viewmodel/zones_viewmodel.py src/viewmodel/channel_utils.py src/operations_with_zones/ZoneItemRepository.py tests/test_zone_save_8ch.py
git commit -m "feat(zones): сохранять present+имена 8 каналов, правило active (create/rename)"
```

---

## Task 5: Панель — галочки active для present-каналов, вертикально

**Files:**
- Modify: `src/ui/custom/zone/ZoneListItem.py`
- Test: `tests/test_zone_list_item_8ch.py`

**Interfaces:**
- Consumes: `subzone1..8`, `subzone1..8_present`, `subzone1..8_name` у `Orange`.
- Produces: панель рисует **интерактивные чекбоксы** только для present-каналов; галочка = active, сохраняется; расположение вертикальное.

- [ ] **Step 1: Переписать _build_subzones на present-каналы с чекбоксами**

Вместо подписей (текущая 4-канальная версия) — для каждого `n` в 1..8, где `subzone{n}_present`, создать `QCheckBox` с подписью `subzone{n}_name or f"Канал {n}"`, `setChecked(subzone{n})`, вертикальный layout. `stateChanged` → обновить `zone.subzone{n}` + `save_zone_state`. Не-present каналы не показывать. Хранить чекбоксы в словаре `self.channel_checks = {n: chk}` для обновления.

- [ ] **Step 2: save_zone_state пишет все 8 + present + имена**

Расширить `save_zone_state`: писать `subzone1..8`, `subzone1..8_present`, `subzone1..8_name` из `self.zone` (циклом). Существующие ключи не переименовывать.

- [ ] **Step 3: update_zone_data перестраивает чекбоксы**

`update_zone_data` должен пересобрать чекбоксы из нового `zone` (present-набор мог измениться). Убрать все прежние ссылки на `subzone1_checkbox`/`subzone2_checkbox` (4-канальные), заменить на словарь.

- [ ] **Step 4: Offscreen-тест панели**

`tests/test_zone_list_item_8ch.py`: зона с present-каналами 1 и 5 (имена «улица»/«склад»), 1 active, 5 не active → в контейнере ровно 2 чекбокса с этими подписями, у канала 1 стоит галочка, у 5 нет; не-present каналов нет. Прогнать весь набор.

- [ ] **Step 5: Скриншот через qt-testing**

Панель зоны с present-каналами 1,3,5 (разные имена), часть active → видно 3 чекбокса вертикально, галочки отражают active. Проверить, что не-present не показаны, и горизонтального скролла нет.

- [ ] **Step 6: Commit**

```bash
git add src/ui/custom/zone/ZoneListItem.py tests/test_zone_list_item_8ch.py
git commit -m "feat(ui): панель — галочки active для present-каналов, вертикально"
```

---

## Task 6: Валидация — минимум 1 present-канал

**Files:**
- Modify: `src/ui/fragments/UI_AddZoneWindow.py` (validate_and_accept)

**Interfaces:**
- Consumes: `get_channels()`.
- Produces: окно не сохраняется, если не отмечен ни один present-канал.

- [ ] **Step 1: Обновить проверку**

В `validate_and_accept` (после проверки имени, до `accept()`) — проверка на present (в 4-канальной версии проверка была на активный канал; теперь считаем present):

```python
        if not any(present for present, _ in self.get_channels()):
            QMessageBox.information(self, 'Уведомление.', 'Выберите хотя бы один канал у устройства!')
            return
```

- [ ] **Step 2: Тест + проверка**

Обновить/добавить в `tests/test_add_zone_window.py`: без единого present-канала `validate_and_accept()` не принимает (QMessageBox замокать); с ≥1 present + непустым именем — принимает. Прогнать весь набор → PASS.

- [ ] **Step 3: Commit**

```bash
git add src/ui/fragments/UI_AddZoneWindow.py tests/test_add_zone_window.py
git commit -m "feat(ui): требовать минимум один present-канал у устройства"
```

---

## Task 7: Сервер — parse_play_variant до 1..8 (репо sg_orange_2026-)

**Files:**
- Modify: `sg_orange_2026-/play_variant_parser.py`
- Modify: `sg_orange_2026-/tests/test_play_variant_parser.py`

**Interfaces:**
- Produces: `parse_play_variant` принимает номера линий 1..8 (было 1..4).

**Важно:** делать в репо `sg_orange_2026-` на ветке `feature/zone-4-channels` **поверх свежего `origin/feature/zone-4-channels` (коммит e2f8a93 от sun0)** — сначала `git fetch` + свериться. Предупредить sun0, что трогаем файл.

- [ ] **Step 1: Синхронизироваться с веткой sun0**

```bash
cd ../sg_orange_2026-
git fetch origin
git checkout feature/zone-4-channels
git log --oneline -1 origin/feature/zone-4-channels   # ожидаем e2f8a93 (или новее)
git merge --ff-only origin/feature/zone-4-channels 2>/dev/null || git rebase origin/feature/zone-4-channels
```

- [ ] **Step 2: Написать падающий тест на 5..8**

Добавить в `tests/test_play_variant_parser.py`:

```python
    def test_channels_5_to_8(self):
        self.assertEqual(parse_play_variant("5,6,7,8"), [5, 6, 7, 8])
    def test_mixed_1_to_8(self):
        self.assertEqual(parse_play_variant("1,5,8"), [1, 5, 8])
    def test_out_of_range_high_9(self):
        self.assertEqual(parse_play_variant("9"), [])
```

- [ ] **Step 3: Прогнать — FAIL** (сейчас `5..8` режутся диапазоном 1..4)

Run: `python3 -m unittest tests.test_play_variant_parser -v`
Expected: FAIL на `test_channels_5_to_8`.

- [ ] **Step 4: Расширить диапазон**

В `play_variant_parser.py` изменить одну строку:

```python
            if 1 <= n <= 8:
                result.append(n)
```

- [ ] **Step 5: Прогнать — PASS**

Run: `python3 -m unittest tests.test_play_variant_parser -v`
Expected: PASS (старые + новые).

- [ ] **Step 6: Commit** (в `sg_orange_2026-`)

```bash
git add play_variant_parser.py tests/test_play_variant_parser.py
git commit -m "feat(server): parse_play_variant принимает каналы 1..8"
```

---

## Self-Review

- **Покрытие спека:** данные+миграция (T1), active=present∧active + 1..8 (T2), окно 8 вертикаль (T3), сохранение present+правило active (T4), панель галочки present вертикаль (T5), валидация min-1 present (T6), сервер 1..8 (T7). Все разделы спека покрыты.
- **Совместимость:** T1 только добавляет ключи; present-дефолты 1,2=True сохраняют старые зоны. ✓
- **Типы/имена:** `active_channels`/`format_play_variant`/`resolve_active` (T2,T4) → используются в T4/T5; `get_channels()` 8 пар (T3) → T4/T6; `parse_play_variant` 1..8 (T7). Согласованы.
- **Формат:** строка, не массив (T2 format_play_variant без изменений). ✓
- **Вне плана:** серверная маршрутизация/ESP32 `rel1..rel4` — sun0 (в плане только parse 1..8).
