#!/usr/bin/env python3
__author__ = 'Sergey Maksimov'
__mail__ = 'm6v@mail.ru'
__version__ = '1.0'
__date__ = '2024-10-24'
__copyright__ = 'Copyright © 2024 Sergey Maksimov'
__licence__ = 'GNU Public Licence (GPL) v3'

import os
import sys
from PyQt5.Qt import QApplication

from MainWindow import MainWindow

if __name__ == '__main__':
    '''
    # Попытка сделать запуск с правами root'а неудачная, выдает сообщение об ошибке
    if os.getuid() != 0:
        # args = ['pkexec'] + [sys.executable] + sys.argv
        DISPLAY = os.environ['DISPLAY']
        XAUTHORITY = os.environ['XAUTHORITY']
        args = ['pkexec'] + [__file__] + sys.argv
        # os.execlp(args[0], *args)
        os.execlpe(args[0], *args, {'DISPLAY': DISPLAY, 'XAUTHORITY': XAUTHORITY, 'XDG_RUNTIME_DIR': '/tmp/runtime-root'})
    else:
    '''
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
