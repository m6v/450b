#!/usr/bin/env python3
__author__ = 'Sergey Maksimov'
__mail__ = 'm6v@mail.ru'
__version__ = '1.2'
__date__ = '2024-10-24'
__copyright__ = 'Copyright © 2024 Sergey Maksimov'
__licence__ = 'GNU Public Licence (GPL) v3'

import os
import sys
from PyQt5.Qt import QApplication

from MainWindow import MainWindow

if __name__ == '__main__':
    if os.getuid() != 0:
        # В Astra Linux использовать fly-su, в других ОС pkexec
        if os.path.isfile('/usr/bin/fly-su'):
            args = ['fly-su'] + [os.path.abspath(__file__)] + sys.argv
        else:
            args = ['pkexec'] + [os.path.abspath(__file__)] + sys.argv
        os.execlp(args[0], *args)
    else:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
