#!/usr/bin/env python3
__author__ = 'Sergey Maksimov'
__mail__ = 'm6v@mail.ru'
__version__ = '1.2'
__date__ = '2024-10-24'
__copyright__ = 'Copyright © 2024 Sergey Maksimov'
__licence__ = 'GNU Public Licence (GPL) v3'

import configparser
import os
import sys
from PyQt5.Qt import QApplication

from MainWindow import MainWindow

if __name__ == '__main__':

    # При запуске упакованного исходника ресурсы, распаковываются во временный каталог,
    # указанный в sys._MEIPASS, в этом случае путь к исходному каталогу взять из sys.executable
    if hasattr(sys, "_MEIPASS"):
        INITIAL_DIR = os.path.dirname(sys.executable)
    else:
        INITIAL_DIR = os.path.dirname(os.path.realpath(__file__))
    
    config = configparser.ConfigParser(allow_no_value = True)
    config.read(os.path.join(INITIAL_DIR, 'config.ini'))
    run_as_root = int(config.get('general', 'root', fallback='0'))
        
    if run_as_root and os.getuid() != 0:
        # В Astra Linux использовать fly-su, в других ОС pkexec
        if os.path.isfile('/usr/bin/fly-su'):
            args = ['fly-su'] + [os.path.realpath(__file__)] + sys.argv
        else:
            args = ['pkexec'] + [os.path.realpath(__file__)] + sys.argv
        os.execlp(args[0], *args)
    else:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
