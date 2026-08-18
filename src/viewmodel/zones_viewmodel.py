"""
ZonesViewModel — логика фичи «Зоны» (сетевое подключение, MQTT, статусы).

Phase 2, Task 6: методы перенесены из MainWindow VERBATIM.
ВСЕ зональные объекты (ZONE_LIST, zones_repo, status_api, connection_thread,
system_checker, layout_manager) остаются на View — доступ через self.view.<attr>.
ZonesViewModel.__init__ ЛЁГКИЙ: только self.view.
"""
import logging
import subprocess

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QDialog, QMessageBox

from src.data.OrangeStatus import OrangeStatus
from src.data.ZoneModel import Orange
from src.ui.fragments.UI_AddZoneWindow import UI_AddZoneWindow
from src.utils.logger_config import setup_logger
from time import sleep

logger = setup_logger()


class ZonesViewModel(QObject):
    """ViewModel для фичи «Зоны». Принимает ссылку на View для доступа к
    виджетам и зональным объектам (остаются на View)."""

    def __init__(self, view):
        super().__init__()
        self.view = view
        # NOTE: self.view.ZONE_LIST / zones_repo / status_api / connection_thread /
        # system_checker создаются ПОЗЖЕ в MainWindow.__init__ — не обращаться
        # к ним здесь, только внутри методов.

    # ------------------------------------------------------------------
    # Методы перенесены из MainWindow VERBATIM (self.<attr> → self.view.<attr>
    # для атрибутов, принадлежащих View; виджеты также через self.view).
    # ------------------------------------------------------------------

    def launch_system_checker(self):
        if not self.view.system_checker.isRunning():
            self.view.system_checker.start()

    def launch_status_connection(self):
        self.view.zone_refresh_btn.setEnabled(False)
        self.view.zone_process_indicator.setVisible(True)
        self.view.zone_process_indicator.indicate()
        if not self.view.connection_thread.isRunning():
            logger.info(f"main: launch_status_connection")
            self.view.connection_thread.start()

    @pyqtSlot(bool, str)
    def update_online_status(self, is_online: bool, ip: str):
        for zone in self.view.ZONE_LIST:
            if ip == zone.ip:
                zone.is_online = is_online
        self.update_zones()

    def update_statuses(self):
        self.view.commit_orange_command(command="status", thread_list=self.view.play_threads)
        for zone in self.view.ZONE_LIST:
            zone.is_online = self.view.status_api.is_online(zone.ip)
            logger.info(f"main: on_connected {zone.name} - {zone.is_online}")
        # self.update_zones()
        if not self.view.status_sender.isRunning():
            self.view.status_sender.start()
        self.view.zone_refresh_btn.setEnabled(True)
        self.view.zone_process_indicator.setVisible(False)
        self.view.zone_process_indicator.stopIndicate()

    def on_connected(self):
        logger.info(f"main: on_connected")
        self.view.commit_orange_command(command="status", thread_list=self.view.play_threads)
        for zone in self.view.ZONE_LIST:
            logger.info(f"main: on_connected {zone.name} - {zone.is_online}")
            self.view.status_api.is_online(zone.ip)
        # self.update_zones()
        self.view.zone_refresh_btn.setEnabled(True)
        self.view.zone_process_indicator.setVisible(False)
        self.view.zone_process_indicator.stopIndicate()
        logger.info(f"main: on_connected self.view.connection_thread.isRunning() - {self.view.connection_thread.isRunning()}")

    def auto_search_zones(self):
        self.view.progressBar.setRange(0, 0)
        self.view.app.processEvents()
        result = subprocess.run(['bash', 'src/SCAN.sh'], stdout=subprocess.PIPE)
        output = result.stdout.decode()
        lines = output.splitlines()

        for line in lines:
            new_zone = Orange(
                ip=line,
                name=f"зона оповещения {line}",
                isChecked=True
            )
            self.view.zones_repo.add_zone(new_zone)

        self.view.progressBar.setRange(0, 100)
        self.view.progressBar.setValue(0)
        self.view.app.processEvents()
        self.update_zones()

    def rename_zone(self, selected_zone: Orange):
        # selected_zone = self.zone_list_widget.get_current_zone()
        if selected_zone is not None:

            for zone in self.view.ZONE_LIST:
                if selected_zone.name == zone.name:
                    channels = [
                        (zone.subzone1, zone.subzone1_name),
                        (zone.subzone2, zone.subzone2_name),
                        (zone.subzone3, zone.subzone3_name),
                        (zone.subzone4, zone.subzone4_name),
                    ]
                    addZoneDialog = UI_AddZoneWindow(zone.name, zone.ip, self.view.ZONE_LIST, channels, True)
                    if addZoneDialog.exec() == QDialog.Accepted:
                        zone.name = addZoneDialog.get_name_field().text()
                        zone.ip = addZoneDialog.get_ip_field().text()
                        ch = addZoneDialog.get_channels()
                        zone.subzone1, zone.subzone1_name = ch[0]
                        zone.subzone2, zone.subzone2_name = ch[1]
                        zone.subzone3, zone.subzone3_name = ch[2]
                        zone.subzone4, zone.subzone4_name = ch[3]

            self.view.zones_repo.save(self.view.ZONE_LIST)

        self.update_zones()

    def add_zone_from_file(self, file_path):
        # Загрузка данных из файла
        self.view.zones_repo.add_zone_from_file(file_path)

        self.update_zones()
        sleep(0.1)

    def add_zone(self):
        addZoneDialog = UI_AddZoneWindow(f'зона {len(self.view.ZONE_LIST) + 1}', '192.168', self.view.ZONE_LIST)

        if addZoneDialog.exec() == QDialog.Accepted:
            logger.info(f"addZoneDialog.ip_field: {addZoneDialog.get_ip_field().text()}")
            logger.info(f"addZoneDialog.name_field: {addZoneDialog.get_name_field().text()}")
            ip_field = addZoneDialog.get_ip_field()
            name_field = addZoneDialog.get_name_field()

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

            if name_field.text() == "" or ip_field.text() == "":
                QMessageBox.information(self.view, 'Уведомление.',
                                        'Введите название зоны!')
            else:
                self.view.zones_repo.add_zone(new_zone)

        self.update_zones()

    def remove_zone(self, selected_zone: Orange):
        try:
            # selected_zone = self.zone_list_widget.get_current_zone()
            self.view.zones_repo.remove_zone(selected_zone)
            self.view.status_api.remove_broker(selected_zone.ip)
        except Exception as e:
            logging.error(f"main: remove_zone{e}")

        self.update_zones()

    #
    #
    def update_zones(self, status=None):
        if status:
            print(f"main: status on upd zonest {status}")

            self.view.status_sender.setStatus(status)
            # self.api_thread.start()

            self.update_zone_status(status)
        else:
            self.view.zone_list_widget.update_zones(self.view.ZONE_LIST)

            #self.update_ui()

    def update_zone_status(self, status):
        for zone in self.view.ZONE_LIST:
            if zone.ip == status.orange_ip:
                zone.is_playing = status.is_playing
                zone.is_streaming = status.is_streaming
                zone.is_sip_running = status.is_sip_running
                zone.is_online = self.view.status_api.is_online(status.orange_ip)
                zone.is_warning = "Error" in status.warn_message
                zone.tooltip_warn_message = status.warn_message
                zone.tooltip_message = status.message
        self.view.zone_list_widget.update_zones(self.view.ZONE_LIST)

    def update_ui(self):
        self.view.update_list_on_slider(self.view.grid_size)
        self.view.zone_list_widget.update_zones(self.view.ZONE_LIST)
        # self.setupUi(self)
        self.view.update()

    @pyqtSlot(OrangeStatus)
    def orange_status_receiver(self, status: OrangeStatus):
        """mqtt"""
        self.update_zones(status)
