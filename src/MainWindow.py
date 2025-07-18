import asyncio
import binascii
import configparser
import functools
import errno
import json
import logging
import os
import socket
import subprocess
import sys
import time
import traceback

from PyQt5 import uic
from PyQt5.Qt import QMainWindow, QAction, QThread, QCursor, QMessageBox, QRect, QFile
from PyQt5.QtCore import Qt, pyqtSignal

import protoproc
import resources

from AddrDialog import AddrDialog
from KeyIdDialog import KeyIdDialog
from KeyParmsDialog import KeyParmsDialog
from PasswdDialog import PasswdDialog
from SettingsDialog import SettingsDialog

INITIAL_DIR = CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
# Если установлена переменная окружения _MEIPASS, то запуск происходит из временного каталога,
# созданного при распаковке бандла. В этом случае путь к исходному каталогу взять из sys.executable
if hasattr(sys, "_MEIPASS"):
    INITIAL_DIR = os.path.dirname(sys.executable)

configfile = os.path.join(INITIAL_DIR, 'config.ini')

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt='%Y-%m-%d %H:%M:%S')


class RecieverThread(QThread):
    trigger = pyqtSignal(bytes)

    def __init__(self, connection):
        super().__init__()
        self.connection = connection

    def run(self):
        while True:
            # Прием квитанции
            data = self.connection.recvfrom(1024)
            reply = data[0]
            addr = data[1]
            self.trigger.emit(reply)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(CURRENT_DIR, 'MainWindow.ui'), self)

        '''
        Вариант с загрузкой формы из файла ресурсов, создаваемого с помощью pyrcc5
        stream = QFile(":MainWindow.ui")
        stream.open(QFile.ReadOnly)
        uic.loadUi(stream, self)
        stream.close()
        Не требует распространения ui-файлов вместе с приложением (только файл ресурсов)
        '''

        self.config = configparser.ConfigParser(allow_no_value=True)
        # Установить чувствительность ключей к регистру
        self.config.optionxform = str
        self.config.read(configfile)

        # Параметр включения режима отладки (вывод дампов отправляемых запросов и принимаемых квитанций в stdout)
        self.debug = int(self.config.get('general', 'debug', fallback='0'))

        try:
            # Разбить строку на элементы, преобразовать их в целые числа и получить QRect с геометрией главного окна
            geometry = QRect(*map(int, self.config.get('window', 'geometry').split(';')))
            # Восстановить геометрию главного окна
            self.setGeometry(geometry)

            state = int(self.config.get('window', 'state'))
            self.restoreState(bytearray(state))
        except configparser.NoOptionError as e:
            logging.warning(e)

        hostname = socket.gethostname()
        # Подсчитать 16-разрядную контр. сумму от hostname и использовать ее в качестве идентификатора программы
        prg_id = binascii.crc_hqx(hostname.encode(), 0)
        self.program_id = prg_id.to_bytes(2, 'big')  # Идентификатор управляющей программы
        self.instruction_number = 0  # Порядковый номер инструкции, увеличивается на единицу после отправки команды

        # Статус изделия
        self.mode = protoproc.WORK

        self.host = self.config.get('network', 'host', fallback='192.168.0.3')
        self.port = int(self.config.get('network', 'port', fallback='4660'))

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recieverThread = RecieverThread(self.sock)
        self.recieverThread.trigger[bytes].connect(self.process_reply)
        self.recieverThread.start()

        self.keyIdDialog = KeyIdDialog(self)
        self.keyParmsDialog = KeyParmsDialog(self)
        self.settingsDialog = SettingsDialog(self, self.config)
        self.passwdDialog = PasswdDialog(self)
        self.addrDialog = AddrDialog(self)

        # Создать элементы меню "Запросы"
        actions = {'Запросить время': protoproc.ask_clock,
                   'Запросить контрольную сумму ПО': protoproc.ask_crc,
                   'Запросить статус первоначального тестирования': protoproc.ask_first_status,
                   'Запросить адрес сервера асинхронных сообщений': protoproc.ask_asynaddress,
                   'Запросить состояние (режим) изделия': protoproc.ask_mode}
        for name, func in actions.items():
            action = QAction(name, self)
            action.triggered.connect(functools.partial(self.send_request, func()))
            self.requestsMenu.addAction(action)

        try:
            # Создать элементы меню "Помощь", в соответствии со словарем help, указанном в файле настроек
            # если путь не указан, то файлы справки должны быть в том же каталоге, что и исполняемые
            actions = json.loads(self.config.get('actions', 'help'))
            for name, fname in actions.items():
                try:
                    # Если абсолютный путь файла справки не задан, пытаемся использовать исходный каталог исполняемого файла
                    if not os.path.isabs(fname):
                        fname = os.path.join(INITIAL_DIR, (fname))
                    if os.path.exists(fname):
                        action = QAction(name, self)
                        action.triggered.connect(functools.partial(self.show_doc, fname))
                        self.helpMenu.addAction(action)
                    else:
                        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), fname)
                except FileNotFoundError as e:
                    logging.error(e)
        except configparser.NoOptionError as e:
            logging.warning(e)

        # Настроить контекстое меню resultsPlainTextEdit
        self.resultsPlainTextEdit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.resultsPlainTextEdit.customContextMenuRequested.connect(self.create_context_menu)

        # Соединить сигналы и слоты
        self.workAreaKeysAction.triggered.connect(functools.partial(self.send_request, protoproc.ask_keys_workspace()))
        self.storageAreaKeysAction.triggered.connect(functools.partial(self.send_request, protoproc.ask_keys_storage()))

        self.inputKeyAction.triggered.connect(self.input_key)
        self.eraseKeyAction.triggered.connect(self.erase_key)
        self.outputKeyAction.triggered.connect(self.output_key)
        self.setClockAction.triggered.connect(self.set_clock)
        self.generateKeyAction.triggered.connect(self.generate_key)
        self.showSettingsAction.triggered.connect(self.settingsDialog.exec)
        self.changePasswdAction.triggered.connect(self.set_admin_password)
        self.showKeysNumberAction.triggered.connect(self.show_keys_number)
        self.resetDeviceAction.triggered.connect(self.reset_all)
        self.setAddrAction.triggered.connect(self.set_address)

        # Если пароль не хранится в настройках, запрашиваем его при запуске программы
        self.passwd = bytearray(self.config.get('general', 'passwd', fallback=''), 'utf-8')
        if not self.passwd:
            while True:
                passwd = self.passwdDialog.exec()
                if passwd:
                    break
            self.passwd = bytearray(passwd, 'utf-8')

        # Запросить текущий режим, чтобы правильно выставить выпадающий список
        self.send_request(protoproc.ask_mode())

        self.modeComboBox.currentIndexChanged.connect(self.mode_changed)

    def send_request(self, body):
        '''Отправка запроса'''
        header = self.program_id + self.instruction_number.to_bytes(2, 'big') + self.passwd
        if self.debug:
            print('Send to %s:%s' % (self.host, self.port))
            protoproc.hexdump(header + body)
        try:
            self.sock.sendto(header + body, (self.host, self.port))
            self.instruction_number += 1
        except OSError as e:
            QMessageBox.critical(self, 'Ошибка', str(e))

    def show_message(self, *results, sep=' '):
        '''Вывод сообщений с предварительным преобразованием всех элементов в строки'''
        self.resultsPlainTextEdit.appendPlainText(sep.join(str(x) for x in results))

    def process_reply(self, reply):
        '''Обработка квитанции'''
        if self.debug:
            print('Recieve from')
            protoproc.hexdump(reply)
        try:
            # Вызов функции обработки квитанций (второй параметр - функция вывода результатов обработки)
            # Функция возвращает None или словарь с параметрами
            result = protoproc.parse_reply(reply, self.show_message)
            if result['mode'] is not None:
                self.mode = result['mode']
                self.modeComboBox.setCurrentIndex(self.mode)
                self.keysMenu.setEnabled(self.mode == protoproc.REGLAMENT)
        except Exception as e:
            logging.warning(traceback.format_exc())

    def mode_changed(self, index):
        '''Отправить запрос на изменение режима работы'''
        if index != self.mode:
            self.send_request(protoproc.set_mode(index))
            self.mode = index
            # Если находимся в режиме "Регламент", включить меню "Ключи", иначе выключить
            self.keysMenu.setEnabled(self.mode == protoproc.REGLAMENT)

    def input_key(self):
        '''Вывести диалоговое окно ввода идентификатора ключа и отправить запрос на ввод ключа'''
        key_id = self.keyIdDialog.exec()
        if key_id:
            self.send_request(protoproc.input_key(key_id))

    def erase_key(self):
        '''Вывести диалоговое окно ввода идентификатора ключа и отправить запрос на стирание ключа'''
        key_id = self.keyIdDialog.exec()
        if key_id:
            self.send_request(protoproc.erase_key(key_id))

    def output_key(self):
        '''Вывести диалоговое окно ввода идентификатора ключа и отправить запрос на вывод ключа'''
        key_id = self.keyIdDialog.exec()
        if key_id:
            self.send_request(protoproc.output_key(key_id))

    def show_keys_number(self):
        '''Отправить запрос о количестве ключей'''
        self.send_request(protoproc.ask_keys_number())

    def set_clock(self):
        '''Отправить запрос об установке времени'''
        self.send_request(protoproc.set_clock())

    def generate_key(self):
        '''Вывести диалоговое окно ввода параметров ключа и отправить запрос на генерацию ключа'''
        key = self.keyParmsDialog.exec()
        if not key:
            return

        self.setCursor(QCursor(Qt.WaitCursor))

        logging.info('set_mode(KEYGEN)')
        self.send_request(protoproc.set_mode(protoproc.KEYGEN))
        time.sleep(10)
        logging.info('set_clock')
        self.send_request(protoproc.set_clock())
        time.sleep(10)
        logging.info('set_mode(REGLAMENT)')
        self.send_request(protoproc.set_mode(protoproc.REGLAMENT))
        time.sleep(10)
        logging.info('gen_key')
        self.send_request(protoproc.gen_key(key))
        time.sleep(10)
        # Чтобы устройство реагировало на запросы, нужно переключить его в режим "Работа",
        # выдержать паузу 5-20 сек и снова установить время!
        logging.info('set_mode(WORK)')
        self.send_request(protoproc.set_mode(protoproc.WORK))
        time.sleep(10)
        logging.info('set_clock')
        self.send_request(protoproc.set_clock())

        self.setCursor(QCursor(Qt.ArrowCursor))
        self.modeComboBox.setCurrentIndex(0)

    def set_admin_password(self):
        '''Дважды запросить новый пароль и, если они совпадают, отпавить запрос на смену пароля'''
        passwd = self.passwdDialog.exec('Введите новый пароль (до 12 цифр)')
        if not passwd:
            return False
        confrm = self.passwdDialog.exec('Подтвердите новый пароль (до 12 цифр)')
        if not confrm:
            return False
        if passwd != confrm:
            QMessageBox.critical(self, 'Ошибка', 'Пароли не совпадают!')
            return False
        self.send_request(protoproc.set_admin_password(self.passwd, bytearray(passwd, 'utf-8')))
        self.passwd = bytearray(passwd, 'utf-8')
        return self.passwd

    def set_address(self):
        '''Установка IP-адресов интерфейсов изделия'''
        iface = self.addrDialog.exec()
        # Здесь сравниваем именно с False, т.к. iface может принимать и нулевое значение
        if iface is False:
            return
        try:
            ip = self.addrDialog.ip
            socket.inet_aton(ip)
            if iface == protoproc.INT_LAN:
                # Установка IP-адреса интерфейса ЛВС изделия
                self.send_request(protoproc.set_address(protoproc.INT_LAN, ip))
                self.host = ip
                self.config.set('network', 'host', ip)
                QMessageBox.warning(self, 'Предупреждение', 'Для вступления изменений в силу, перезапустите программу')
            elif iface == protoproc.INT_WAN:
                # Установка IP-адреса интерфейса ВВС изделия
                self.send_request(protoproc.set_address(protoproc.INT_WAN, ip))
            elif iface == protoproc.EXT_ASINC_SRV:
                # Установка IP-адреса сервера асинхронных сообщений
                port = int(self.addrDialog.port)
                self.send_request(protoproc.set_address(protoproc.EXT_ASINC_SRV, ip, port))
            else:
                raise ValueError("Неправильный идентификатор интерфейса")
        except socket.error:
            QMessageBox.critical(self, 'Ошибка', 'Введен неправильный ip-адрес')
        except (IndexError, ValueError):
            QMessageBox.critical(self, 'Ошибка', 'Не введен или введен неправильный номер порта')

    def reset_all(self):
        '''Отправить запрос на сброс устройства'''
        # В Astra Linux SE 1.6.10 QMessageBox.StandardButton не имеет атрибута Yes, поэтому используем не QMessageBox.StandardButton.Yes, а QMessageBox.Yes
        if QMessageBox.question(self, 'Внимание', 'После выполнения команды вся информация в запоминающем устройстве изделия будет стерта! Продолжить?') == QMessageBox.Yes:
            self.send_request(protoproc.reset_all())
            time.sleep(2)
            self.send_request(protoproc.set_clock())
            # Дефолтный пароль после сброса устройства
            self.passwd = bytearray('000000000000', 'utf-8')
            while not self.set_admin_password():
                pass

    def create_context_menu(self):
        self.resultsPlainTextEdit.menu = self.resultsPlainTextEdit.createStandardContextMenu()
        self.resultsPlainTextEdit.menu.addAction('Очистить все', self.resultsPlainTextEdit.clear)
        self.resultsPlainTextEdit.menu.exec_(QCursor.pos())

    def show_doc(self, fname):
        '''Запустить ассоциированное внешнее приложение для просмотра справочного файла'''
        subprocess.run(['xdg-open', fname])

    def closeEvent(self, e):
        '''Сохранить геометрию, состояние главного окна и пароль'''
        # self.config.read(configfile)
        # Получить кортеж с элементами QRect геометрии главного окна
        geometry = self.geometry().getRect()
        # Преобразовать элементы кортежа в строки и разделить символом ';'
        self.config.set('window', 'geometry', ';'.join(map(str, geometry)))
        self.config.set('window', 'state', str(int(self.windowState())))
        # Если установлена опция "хранить пароль в настройках", сохранить его
        if self.settingsDialog.get_passwd_store_politic():
            self.config.set('general', 'passwd', self.passwd.decode())
        else:
            self.config.set('general', 'passwd', '')
        with open(configfile, 'w') as file:
            self.config.write(file)

        self.sock.close()
