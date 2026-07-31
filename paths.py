import logging
import os
logger = logging.getLogger(__name__)
current_dir = os.getcwd()
sep = os.sep
img_files = f'res{sep}IMAGES'
ogg_files = f'res{sep}yandex{sep}ogg'
mp3_files = f'res{sep}yandex{sep}mp3'  # os.path.join(current_dir, r'yandex\mp3')
zones_json = f'res{sep}json{sep}zones.json'  # os.path.join(current_dir, r'yandex\mp3')
data_scenaries_json = f'res{sep}json{sep}data_scenaries.json'  # os.path.join(current_dir, r'yandex\mp3')
scenario=f'res{sep}json{sep}scenario.json'
shedule_data_scenaries= f'res{sep}json{sep}shedule_data_scenaries{sep}'
settings = f'res{sep}json{sep}settings.json'
tcp_timeout = f'INI{sep}tcp_timeout.txt'
crc_try = f'INI{sep}crc_try.txt'
vol = f'INI{sep}vol.txt'
grid = f'INI{sep}grid.txt'
project = f'INI{sep}project.txt'
log_file = f'logs{sep}ksb_SG.log'
DIAG_TONE_FREQ = 1000  # частота диагностического тона (Гц), Ctrl+Shift+T

logger.info(f'init paths :\n{mp3_files}\n{img_files}\n{data_scenaries_json}\n{zones_json}\n{ogg_files}\n')
logger.info(f'current_dir - {current_dir}')
