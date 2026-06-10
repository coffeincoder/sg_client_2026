import json
import logging
from time import sleep

from PyQt5.QtWidgets import QListWidget

import paths
from src.utils.NetWorkScanner import *
from src.ui.fragments.UI_AddZoneWindow import *

logger = logging.getLogger(__name__)
def get_mac_address(s):
    mac_address_pattern = r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b'
    match = re.search(mac_address_pattern, s)
    if match:
        return match.group()
    return None


def get_ip_address(s):
    ip_address_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    match = re.search(ip_address_pattern, s)
    if match:
        return match.group()
    return None


class SearchDevices(QDialog):

    def add(self):
        ip = self.list_widget.currentItem().text()
        addZoneDialog = UI_AddZoneWindow('', ip)
        if addZoneDialog.exec() == QDialog.Accepted:
            print(addZoneDialog.getFields())
            fields = addZoneDialog.getFields()
            # добавляю zone_name,zone_IP в файл json

            with open(paths.zones_json, 'r', encoding='UTF-8') as file:
                file.seek(0)
                data = file.read()
                if data:
                    existing_data = json.loads(data)
                else:
                    existing_data = []

                new_data = {
                    "name": fields[0],
                    "ip": fields[1],
                    "isChecked": True
                }
                if fields[0] != '':
                    existing_data.append(new_data)

                    with open(paths.zones_json, 'w') as file:
                        json.dump(existing_data, file)


                else:
                    QMessageBox.information(self, 'Уведомление.',
                                            'Введите название зоны!')

            sleep(0.1)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # Создание кнопки "Добавить"
        self.list_widget = QListWidget()
        self.add_button = QPushButton('Добавить')
        self.add_button.clicked.connect(self.add)
        # Создание кнопки "Закрыть"
        self.close_button = QPushButton('Закрыть')

        # Создание вертикального макета и добавление виджетов
        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        layout.addWidget(self.add_button)
        layout.addWidget(self.close_button)

        self.setLayout(layout)
        self.setWindowTitle('Устройства в локальной сети')
        result = subprocess.run(['bash', 'src/SCAN.sh'], stdout=subprocess.PIPE)

        # Вывод результата работы скрипта
        output = result.stdout.decode()

        # Разбивка результата на строки
        lines = output.splitlines()
        for line in lines:
            self.list_widget.addItem(line)
