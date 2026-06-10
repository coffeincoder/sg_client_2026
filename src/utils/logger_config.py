import logging
import os

import paths


def setup_logger():
    log_file = paths.log_file
    log_dir = os.path.dirname(log_file)

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    if not os.path.exists(log_file):
        open(log_file, 'w').close()
    logging.basicConfig(
        filename=log_file,
        filemode='a',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',

    )
    return logging.getLogger()
