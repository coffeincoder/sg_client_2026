# 4 канала в окне зоны — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Расширить окно зоны с 2 до 4 «каналов» (чекбокс активности + имя), сохранять их, показывать активные в панели и слать серверу список активных линий.

**Architecture:** Клиент (PyQt5, MVVM) хранит зоны в `zones.json` (dataclass `Orange`). «Канал N» в UI = физическая линия `outN` на сервере (1:1). Протокол `play_variant` переходит со строк-комбинаций на список активных линий `"1,3,4"`; сервер понимает и новый формат, и старые строки.

**Tech Stack:** Python 3.12, PyQt5, `unittest` (встроенный) для логики, `qt-testing` скилл для окон. Сервер: Python 3.11 на Orange Pi (GPIO), тестирует разработчик.

**Spec:** `docs/superpowers/specs/2026-08-16-zone-4-channels-design.md`

## Global Constraints

- **Совместимость флота (~100 клиентов):** НЕ переименовывать существующие ключи `subzone1/subzone2/subzone1_name/subzone2_name`. Новые поля только добавлять с дефолтами (migrate-on-load через `.get(...)`).
- **UI-подпись:** каналы в окне подписываются «Канал 1»…«Канал 4» (не «Линия»).
- **Маппинг:** «Канал N» → `outN`, строго 1:1.
- **Формат протокола:** `{"command":"play_variant","value":"1,3,4"}` — номера активных линий через запятую, `""` = ни одной.
- **Совместимость протокола:** сервер продолжает понимать `channel_1`, `channel_2`, `channel_1_2`.
- **Источник звука:** всегда Orange; выбор источника в окне НЕ добавляем.
- **UI-правила:** без эмодзи, крупные контролы (правило для пожилых дежурных).
- **Прогон тестов:** `.venv/bin/python -m unittest <module> -v` из корня `sg_client_2026`.

---

## Task 0: Ветка и коммит спека

**Files:**
- Commit: `docs/superpowers/specs/2026-08-16-zone-4-channels-design.md`, `docs/superpowers/plans/2026-08-16-zone-4-channels.md`

- [ ] **Step 1: Создать ветку под задачу**

```bash
cd sg_client_2026
git checkout -b feature/zone-4-channels
```

- [ ] **Step 2: Закоммитить спек и план**

```bash
git add docs/superpowers/specs/2026-08-16-zone-4-channels-design.md docs/superpowers/plans/2026-08-16-zone-4-channels.md
git commit -m "docs: спек и план для 4 каналов в окне зоны"
```

---

## Task 1: Данные — поля subzone3/subzone4

**Files:**
- Modify: `src/data/ZoneModel.py:17-20`
- Modify: `src/operations_with_zones/ZoneItemRepository.py:59-62`
- Test: `tests/test_zone_model.py`

**Interfaces:**
- Produces: `Orange` получает поля `subzone3: bool`, `subzone4: bool`, `subzone3_name: str`, `subzone4_name: str` (дефолты `False`/`""`). Репозиторий читает их через `.get("subzone3", False)` и т.д.

- [ ] **Step 1: Написать падающий тест**

```python
# tests/test_zone_model.py
import unittest
from src.data.ZoneModel import Orange


class TestZoneModelChannels(unittest.TestCase):
    def test_new_channels_default_off(self):
        z = Orange()
        self.assertEqual(z.subzone3, False)
        self.assertEqual(z.subzone4, False)
        self.assertEqual(z.subzone3_name, "")
        self.assertEqual(z.subzone4_name, "")

    def test_to_json_includes_new_channels(self):
        z = Orange(subzone3=True, subzone3_name="улица")
        d = z.to_json()
        self.assertTrue(d["subzone3"])
        self.assertEqual(d["subzone3_name"], "улица")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Прогнать — убедиться, что падает**

Run: `.venv/bin/python -m unittest tests.test_zone_model -v`
Expected: FAIL — `AttributeError: 'Orange' object has no attribute 'subzone3'`.

- [ ] **Step 3: Добавить поля в dataclass**

В `src/data/ZoneModel.py` после `subzone2_name`:

```python
    subzone1: bool = False
    subzone2: bool = False
    subzone3: bool = False
    subzone4: bool = False
    subzone1_name: str = ""
    subzone2_name: str = ""
    subzone3_name: str = ""
    subzone4_name: str = ""
```

- [ ] **Step 4: Читать новые поля в репозитории (migrate-on-load)**

В `src/operations_with_zones/ZoneItemRepository.py`, где создаётся `Orange(...)` из `zone_data` (около строки 59), добавить:

```python
                subzone1=zone_data.get("subzone1", False),
                subzone2=zone_data.get("subzone2", False),
                subzone3=zone_data.get("subzone3", False),
                subzone4=zone_data.get("subzone4", False),
                subzone1_name=zone_data.get("subzone1_name", ""),
                subzone2_name=zone_data.get("subzone2_name", ""),
                subzone3_name=zone_data.get("subzone3_name", ""),
                subzone4_name=zone_data.get("subzone4_name", ""),
```

- [ ] **Step 5: Прогнать — убедиться, что прошёл**

Run: `.venv/bin/python -m unittest tests.test_zone_model -v`
Expected: PASS.

- [ ] **Step 6: Проверить обратную совместимость вручную**

Запустить приложение на СТАРОМ `zones.json` (где нет ключей subzone3/4) и убедиться, что оно грузится без ошибок (поля становятся `False`/`""`).

Run: `.venv/bin/python main.py`

- [ ] **Step 7: Commit**

```bash
git add src/data/ZoneModel.py src/operations_with_zones/ZoneItemRepository.py tests/test_zone_model.py
git commit -m "feat(data): поля subzone3/subzone4 с migrate-on-load"
```

---

## Task 2: Логика активных линий (чистая функция)

**Files:**
- Create: `src/viewmodel/channel_utils.py`
- Test: `tests/test_channel_utils.py`

**Interfaces:**
- Produces:
  - `active_channels(zone: Orange) -> list[int]` — номера активных каналов 1..4.
  - `format_play_variant(channels: list[int]) -> str` — `"1,3,4"`, пусто `""`.

- [ ] **Step 1: Написать падающий тест**

```python
# tests/test_channel_utils.py
import unittest
from src.data.ZoneModel import Orange
from src.viewmodel.channel_utils import active_channels, format_play_variant


class TestChannelUtils(unittest.TestCase):
    def test_active_channels_mixed(self):
        z = Orange(subzone1=True, subzone2=False, subzone3=True, subzone4=True)
        self.assertEqual(active_channels(z), [1, 3, 4])

    def test_active_channels_none(self):
        z = Orange()
        self.assertEqual(active_channels(z), [])

    def test_format_play_variant(self):
        self.assertEqual(format_play_variant([1, 3, 4]), "1,3,4")
        self.assertEqual(format_play_variant([]), "")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Прогнать — убедиться, что падает**

Run: `.venv/bin/python -m unittest tests.test_channel_utils -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.viewmodel.channel_utils'`.

- [ ] **Step 3: Реализовать модуль**

```python
# src/viewmodel/channel_utils.py
from src.data.ZoneModel import Orange


def active_channels(zone: Orange) -> list:
    """Номера активных каналов зоны (1..4)."""
    return [n for n in (1, 2, 3, 4) if getattr(zone, f"subzone{n}")]


def format_play_variant(channels: list) -> str:
    """Список активных линий в строку протокола: [1,3,4] -> '1,3,4', [] -> ''."""
    return ",".join(str(n) for n in channels)
```

- [ ] **Step 4: Прогнать — убедиться, что прошёл**

Run: `.venv/bin/python -m unittest tests.test_channel_utils -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/viewmodel/channel_utils.py tests/test_channel_utils.py
git commit -m "feat(viewmodel): active_channels + format_play_variant"
```

---

## Task 3: Отправка нового формата в playback + фикс бага

**Files:**
- Modify: `src/viewmodel/playback_viewmodel.py:117-137`
- Test: `tests/test_playback_variant.py`

**Interfaces:**
- Consumes: `active_channels`, `format_play_variant` из Task 2.
- Produces: `OrangeWorkerTCP` получает `play_variant` в виде строки `"1,3,4"` (или `""`).

- [ ] **Step 1: Написать падающий тест на сборку значения**

```python
# tests/test_playback_variant.py
import unittest
from src.data.ZoneModel import Orange
from src.viewmodel.channel_utils import active_channels, format_play_variant


class TestPlaybackVariant(unittest.TestCase):
    def test_variant_string_from_zone(self):
        z = Orange(subzone1=True, subzone2=False, subzone3=True, subzone4=False)
        value = format_play_variant(active_channels(z))
        self.assertEqual(value, "1,3")

    def test_variant_empty_when_no_channels(self):
        z = Orange()
        self.assertEqual(format_play_variant(active_channels(z)), "")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Прогнать — убедиться, что проходит (функции уже есть)**

Run: `.venv/bin/python -m unittest tests.test_playback_variant -v`
Expected: PASS (тест фиксирует контракт, который используем ниже).

- [ ] **Step 3: Заменить сборку `_play_variant` в playback_viewmodel**

В `src/viewmodel/playback_viewmodel.py` заменить блок с `if zone.subzone1 and zone.subzone2: ...` (строки ~118-126, где есть баг с двойным `subzone2`) на:

```python
                from src.viewmodel.channel_utils import active_channels, format_play_variant
                _play_variant = format_play_variant(active_channels(zone))
```

(остальной вызов `OrangeWorkerTCP(..., play_variant=_play_variant, ...)` не меняется).

- [ ] **Step 4: Прогнать все тесты**

Run: `.venv/bin/python -m unittest discover -s tests -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/viewmodel/playback_viewmodel.py tests/test_playback_variant.py
git commit -m "feat(playback): слать список активных линий + фикс no_channel"
```

---

## Task 4: Окно зоны — 4 канала с чекбоксами

**Files:**
- Modify: `src/ui/fragments/UI_AddZoneWindow.py` (весь класс)

**Interfaces:**
- Consumes: ничего нового.
- Produces:
  - Конструктор: `UI_AddZoneWindow(zone_name, ip, all_zones, channels=None, for_rename=False)`, где `channels` — список из 4 кортежей `(active: bool, name: str)` (по умолчанию все `(False, "")`).
  - `get_channels() -> list[tuple[bool, str]]` — 4 пары (галочка, имя) в порядке каналов 1..4.

- [ ] **Step 1: Переписать окно на 4 канала**

В `UI_AddZoneWindow` заменить два блока «Канал 1/2» на цикл из 4 строк. Каждая строка: `QCheckBox("Канал N")` + `QLineEdit`. Чекбокс через `toggled` включает/выключает поле:

```python
        self.channel_checks = []
        self.channel_fields = []
        for i in range(4):
            chk = QCheckBox(f"Канал {i + 1}")
            fld = QLineEdit()
            fld.setPlaceholderText(f"Введите имя канала {i + 1}")
            active, name = channels[i] if channels else (False, "")
            chk.setChecked(active)
            fld.setText(name)
            fld.setEnabled(active)
            chk.toggled.connect(fld.setEnabled)
            row = 2 + i
            self.input_layout.addWidget(chk, row, 0)
            self.input_layout.addWidget(fld, row, 1)
            self.channel_checks.append(chk)
            self.channel_fields.append(fld)

    def get_channels(self):
        return [(c.isChecked(), f.text()) for c, f in zip(self.channel_checks, self.channel_fields)]
```

Удалить старые `channel1_*/channel2_*` поля и их геттеры/сеттеры.

- [ ] **Step 2: Проверить окно через qt-testing**

Использовать скилл `qt-testing`: отрендерить `UI_AddZoneWindow` offscreen, снять скриншот. Проверить визуально:
- 4 строки «Канал 1»…«Канал 4», у каждой чекбокс + поле;
- при снятой галочке поле серое/заблокировано, при поставленной — активно;
- окно нормально выглядит и на минимальном, и на большом размере.

- [ ] **Step 3: Commit**

```bash
git add src/ui/fragments/UI_AddZoneWindow.py
git commit -m "feat(ui): окно зоны на 4 канала, чекбокс гасит поле имени"
```

---

## Task 5: Сохранение каналов из окна (create + rename)

**Files:**
- Modify: `src/viewmodel/zones_viewmodel.py:103-146`
- Modify: `src/operations_with_zones/ZoneItemRepository.py:90-118` (update_zone_state)

**Interfaces:**
- Consumes: `UI_AddZoneWindow.get_channels()` из Task 4.
- Produces: при создании/переименовании зоны в `Orange` и в `zones.json` пишутся `subzone1..4` + `subzone1..4_name` из окна.

- [ ] **Step 1: Расширить update_zone_state на каналы 3/4**

В `ZoneItemRepository.update_zone_state` добавить параметры `subzone3/subzone4/subzone3_name/subzone4_name` (по образцу существующих 1/2) и присвоения `zone.subzone3 = ...` под `if ... is not None`.

- [ ] **Step 2: Прокинуть каналы в add_zone**

В `zones_viewmodel.add_zone` открыть окно (channels по умолчанию), после `Accepted` собрать `channels = addZoneDialog.get_channels()` и создать зону с ними:

```python
            channels = addZoneDialog.get_channels()
            new_zone = Orange(
                ip=ip_field.text(),
                name=name_field.text(),
                isChecked=True,
                subzone1=channels[0][0], subzone1_name=channels[0][1],
                subzone2=channels[1][0], subzone2_name=channels[1][1],
                subzone3=channels[2][0], subzone3_name=channels[2][1],
                subzone4=channels[3][0], subzone4_name=channels[3][1],
            )
```

- [ ] **Step 3: Прокинуть каналы в rename_zone (редактирование)**

В `zones_viewmodel.rename_zone` передать в окно текущие каналы зоны и после `Accepted` записать обратно `zone.subzoneN`/`zone.subzoneN_name` из `get_channels()`, затем `self.view.zones_repo.save(...)`.

Открытие окна с текущими каналами:

```python
                    channels = [
                        (zone.subzone1, zone.subzone1_name),
                        (zone.subzone2, zone.subzone2_name),
                        (zone.subzone3, zone.subzone3_name),
                        (zone.subzone4, zone.subzone4_name),
                    ]
                    addZoneDialog = UI_AddZoneWindow(zone.name, zone.ip, self.view.ZONE_LIST, channels, True)
```

- [ ] **Step 4: Проверка вручную — сохранение и перезапуск**

1. Запустить `.venv/bin/python main.py`, создать зону, поставить галочки каналов 1 и 3, ввести имена.
2. Закрыть приложение, открыть `res/json/zones.json` — убедиться, что `subzone1=true`, `subzone3=true`, имена на месте, `subzone2/4=false`.
3. Снова запустить — убедиться, что каналы подтянулись.

- [ ] **Step 5: Commit**

```bash
git add src/viewmodel/zones_viewmodel.py src/operations_with_zones/ZoneItemRepository.py
git commit -m "feat(zones): сохранять 4 канала при создании и редактировании зоны"
```

---

## Task 6: Панель зоны — показывать только активные каналы

**Files:**
- Modify: `src/ui/custom/zone/ZoneListItem.py:86-113` (_build_subzones), `:192-206` (update), `:240-260` (save/handlers)

**Interfaces:**
- Consumes: поля `subzone1..4` у `Orange`.
- Produces: в панели рисуются чекбоксы только активных каналов (по их именам); `save_zone_state` пишет все 4 subzone-ключа.

- [ ] **Step 1: Рисовать только активные каналы**

Переписать `_build_subzones`: пройти по каналам 1..4, для активных (`getattr(zone, f"subzone{n}")`) создать чекбокс с подписью `subzoneN_name or f"Канал {n}"`. Неактивные не показывать.

- [ ] **Step 2: Расширить save_zone_state на 4 канала**

В `save_zone_state` добавить запись `zone['subzone3']`, `zone['subzone4']`, `zone['subzone3_name']`, `zone['subzone4_name']` рядом с существующими 1/2.

- [ ] **Step 3: Проверить панель через qt-testing**

Отрендерить `ZoneListItem` для зоны с активными каналами 1 и 3 → в панели видно ровно два канала (с их именами), 2 и 4 не показаны. Проверить на зоне без активных каналов (панель без чекбоксов каналов) и на зоне со всеми 4.

- [ ] **Step 4: Commit**

```bash
git add src/ui/custom/zone/ZoneListItem.py
git commit -m "feat(ui): в панели зоны показываем только активные каналы"
```

---

## Task 7: min-1 канал — валидация в окне

**Files:**
- Modify: `src/ui/fragments/UI_AddZoneWindow.py` (validate_and_accept)

**Interfaces:**
- Consumes: `get_channels()`.
- Produces: окно не закрывается по «сохранить», если не выбран ни один канал — показывает предупреждение.

- [ ] **Step 1: Добавить проверку в validate_and_accept**

В начало (после проверки имени, до `self.accept()`):

```python
        if not any(active for active, _ in self.get_channels()):
            QMessageBox.information(self, 'Уведомление.', 'Выберите хотя бы один канал!')
            return
```

- [ ] **Step 2: Проверить через qt-testing / вручную**

Создать зону, не ставя ни одной галочки, нажать «сохранить» → появляется предупреждение, окно не закрывается. Поставить одну галочку → сохраняется.

- [ ] **Step 3: Commit**

```bash
git add src/ui/fragments/UI_AddZoneWindow.py
git commit -m "feat(ui): требовать минимум один активный канал"
```

---

## Task 8: Сервер — разбор play_variant (старый + новый формат)

**Files:**
- Create: `sg_orange_2026-/play_variant_parser.py`
- Test: `sg_orange_2026-/tests/test_play_variant_parser.py`

**Interfaces:**
- Produces: `parse_play_variant(value: str) -> list[int]` — номера активных линий. Понимает `"1,3,4"`, `""`, и старые `"channel_1"`, `"channel_2"`, `"channel_1_2"`.

- [ ] **Step 1: Написать падающий тест**

```python
# sg_orange_2026-/tests/test_play_variant_parser.py
import unittest
from play_variant_parser import parse_play_variant


class TestParsePlayVariant(unittest.TestCase):
    def test_new_list(self):
        self.assertEqual(parse_play_variant("1,3,4"), [1, 3, 4])

    def test_empty(self):
        self.assertEqual(parse_play_variant(""), [])

    def test_legacy_channel_1(self):
        self.assertEqual(parse_play_variant("channel_1"), [1])

    def test_legacy_channel_2(self):
        self.assertEqual(parse_play_variant("channel_2"), [2])

    def test_legacy_channel_1_2(self):
        self.assertEqual(parse_play_variant("channel_1_2"), [1, 2])

    def test_garbage_is_empty(self):
        self.assertEqual(parse_play_variant("no_channel"), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Прогнать — убедиться, что падает**

Run (из `sg_orange_2026-`): `python3 -m unittest tests.test_play_variant_parser -v`
Expected: FAIL — модуля нет.

- [ ] **Step 3: Реализовать парсер**

```python
# sg_orange_2026-/play_variant_parser.py
_LEGACY = {
    "channel_1": [1],
    "channel_2": [2],
    "channel_1_2": [1, 2],
}


def parse_play_variant(value):
    """Строка протокола -> список активных линий (1..4).

    Понимает новый формат '1,3,4' и старые строки channel_1/channel_2/channel_1_2.
    Пустая строка или мусор -> [].
    """
    if not value:
        return []
    if value in _LEGACY:
        return list(_LEGACY[value])
    result = []
    for part in value.split(","):
        part = part.strip()
        if part.isdigit():
            n = int(part)
            if 1 <= n <= 4:
                result.append(n)
    return result
```

- [ ] **Step 4: Прогнать — убедиться, что прошёл**

Run: `python3 -m unittest tests.test_play_variant_parser -v`
Expected: PASS.

- [ ] **Step 5: Commit** (в репозитории `sg_orange_2026-`)

```bash
cd ../sg_orange_2026-
git add play_variant_parser.py tests/test_play_variant_parser.py
git commit -m "feat(server): parse_play_variant — новый список + старые строки"
```

---

## Task 9: Сервер — применить список к out1..out4

**Files:**
- Modify: `sg_orange_2026-/ServerState.py` (методы с ветками `play_variant==`)
- Modify: `sg_orange_2026-/sg_new.py` (аналогичные ветки)

**Interfaces:**
- Consumes: `parse_play_variant` из Task 8.
- Produces: воспроизведение включает `outN(True)` для каждой активной линии, остальные `False`. Пустой список → все выключены (тишина, без падения).

- [ ] **Step 1: Ввести общий помощник применения линий**

Там, где сейчас цепочки `if self.play_variant=='channel_1_2': out1(True); out2(True)` — заменить на единый вызов. Пример для одного места (`play_realtime`):

```python
        from play_variant_parser import parse_play_variant
        active = parse_play_variant(self.play_variant)
        self.com.orange_to_both_channel()
        for n in (1, 2, 3, 4):
            getattr(self.digital_out_block, f"out{n}")(n in active)
        # индикация: каналы 1/2 — как раньше; 3/4 см. Task 10
        if 1 in active: self.ESP32Commands.zone1_led_on()
        if 2 in active: self.ESP32Commands.zone2_led_on()
```

Применить тот же приём во всех ветках `play_variant==` в `ServerState.py` и `sg_new.py` (воспроизведение и остановка — при остановке `outN(False)` для всех).

- [ ] **Step 2: Прогнать тесты парсера (регресс)**

Run: `python3 -m unittest tests.test_play_variant_parser -v`
Expected: PASS.

- [ ] **Step 3: Проверка на железе — ЗАДАЧА РАЗРАБОТЧИКА**

Отдать разработчику для проверки на Orange Pi: галочки каналов 1/3 → играют линии out1/out3, лампочки 1/2 корректны, старый клиент (строка `channel_1_2`) по-прежнему работает.

- [ ] **Step 4: Commit** (в `sg_orange_2026-`)

```bash
git add ServerState.py sg_new.py
git commit -m "feat(server): включать out1..out4 по списку активных линий"
```

---

## Task 10 (follow-up): Индикация каналов 3/4

**Blocked:** нужен ответ разработчика — какие номера `ledN` на ESP32 соответствуют лампочкам каналов 3 и 4 (первый ряд, 8 лампочек всего). Пока номера неизвестны — не реализуем.

Когда номера известны: добавить `zone3_led_on/off`, `zone4_led_on/off` в `ESP32Commands.py` (по образцу `zone1/zone2`), заодно причесать дубль `mic_led_on` и рассинхрон sync/async номеров led. Подключить в Task 9 (строки индикации 3/4).

---

## Self-Review

- **Покрытие спека:** данные (T1), логика линий (T2), протокол-клиент (T3), окно (T4), сохранение (T5), панель (T6), валидация min-1 (T7), сервер-разбор (T8), сервер-применение (T9), лампочки (T10, отложено с явной причиной). Все разделы спека покрыты.
- **Совместимость:** T1 — только добавление ключей; T8 — старые строки поддержаны. ✓
- **Типы/имена:** `active_channels`/`format_play_variant` (T2) используются в T3; `get_channels()` (T4) — в T5; `parse_play_variant` (T8) — в T9. Согласованы.
- **Открытый пункт:** индикация 3/4 (T10) честно помечена как заблокированная ответом разработчика, а не заглушкой в коде.
