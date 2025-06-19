import binascii
import functools
import os
import socket
import struct
import random
import time
from threading import Thread
from datetime import datetime

from PyQt5 import uic
from PyQt5.Qt import QMainWindow, QAction, QThread, QDateTime, QSettings, QCursor, QMessageBox, QCursor
from PyQt5.QtCore import Qt, pyqtSignal

from AddrDialog import AddrDialog
from KeyIdDialog import KeyIdDialog
from KeyParmsDialog import KeyParmsDialog
from PasswdDialog import PasswdDialog
from SettingsDialog import SettingsDialog

from protoproc import *

DEBUG = True

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_FILE = os.path.join(CURRENT_DIR, 'settings.ini')


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
        
        self.settings = QSettings(SETTINGS_FILE, QSettings.IniFormat)
        
        self.keyIdDialog = KeyIdDialog(self)
        self.keyParmsDialog = KeyParmsDialog(self)
        self.settingsDialog = SettingsDialog(self)
        self.passwdDialog = PasswdDialog(self)
        self.addrDialog = AddrDialog(self)

        # Восстановить геометрию главного окна
        geometry = self.settings.value('MainWindowGeometry')
        if geometry:
            self.restoreGeometry(geometry)
        state = self.settings.value('MainWindowState')
        if state:
            self.restoreState(state)

        # Если пароль не хранится в настройках, запрашиваем его при запуске программы
        self.passwd = self.settings.value('Passwd', '')
        if not self.passwd:
            while True:
                passwd = self.passwdDialog.exec()
                if passwd:
                    break
            self.passwd = bytearray(passwd, 'utf-8')

        # Параметр включения режима отладки (вывод дампов отправляемых запросов и принимаемых квитанций в stdout)
        self.debug = int(self.settings.value('Debug', 0))
        
        hostname = socket.gethostname()
        # Подсчитать 16-разрядную контр. сумму от hostname и использовать ее в качестве идентификатора программы
        prg_id = binascii.crc_hqx(hostname.encode(), 0)
        self.program_id = prg_id.to_bytes(2, 'big') # Идентификатор управляющей программы
        self.instruction_number = 0 # Порядковый номер инструкции, увеличивается на единицу после отправки команды
        
        # Статус изделия
        self.mode = WORK 
        
        self.settings.beginGroup('Common')
        self.host = self.settings.value('Host', '192.168.0.3')
        self.port = int(self.settings.value('Port', '4660'))
        self.settings.endGroup()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recieverThread = RecieverThread(self.sock)
        self.recieverThread.trigger[bytes].connect(self.process_reply)
        self.recieverThread.start()
        
        # Создать элементы меню "Запросы"
        actions = {'Запросить время': ask_clock,
                   'Запросить контрольную сумму ПО': ask_crc,
                   'Запросить статус первоначального тестирования': ask_first_status,
                   'Запросить адрес сервера асинхронных сообщений': ask_asynaddress,
                   'Запросить состояние (режим) изделия': ask_mode}
        for name, func in actions.items():
            action = QAction(name, self)
            action.triggered.connect(functools.partial(self.send_request, func()))
            self.requestsMenu.addAction(action)
        
        # Настроить контекстое меню resultsPlainTextEdit
        self.resultsPlainTextEdit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.resultsPlainTextEdit.customContextMenuRequested.connect(self.create_context_menu)

        # Запросить текущмй режим, чтобы правильно выставить выпадающий список
        self.send_request(ask_mode())
        
        # Соединить сигналы и слоты
        self.workAreaKeysAction.triggered.connect(functools.partial(self.send_request, ask_keys_workspace()))
        self.storageAreaKeysAction.triggered.connect(functools.partial(self.send_request, ask_keys_storage()))

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

        self.modeComboBox.currentIndexChanged.connect(self.mode_changed)

    def send_request(self, body):
        '''Отправка запроса'''
        header = self.program_id + self.instruction_number.to_bytes(2, 'big') + self.passwd
        if self.debug:
            print('Send to %s:%s' % (self.host, self.port) )
            hexdump(header + body)
        try:
            self.sock.sendto(header + body, (self.host, self.port))
            self.instruction_number += 1
        except OSError as e:
            QMessageBox.critical(self, 'Ошибка', str(e))
        
    def show_message(self, *results, sep=' '):
        '''Вывод сообщений с предварительным преобразованием всех элементов в строки'''
        self.resultsPlainTextEdit.appendPlainText(sep.join(str(x) for x in results))

    def process_reply(self, reply):
        '''Вызов функции обработки квитанций с передачей ей функции вывода результатов обработки
           Функция возвращает None или словарь с параметрами'''
        if self.debug:
            print('Recieve')
            hexdump(reply)
        result = parse_reply(reply, self.show_message)
        try:
            if result['mode'] is not None:
                self.mode = result['mode']
                self.modeComboBox.setCurrentIndex(self.mode)
                self.keysMenu.setEnabled(self.mode == REGLAMENT)
        except:
            pass

    def mode_changed(self, index):
        '''Отправить запрос на изменение режима работы'''
        if index != self.mode:
            self.send_request(set_mode(index))
            self.mode = index
            self.keysMenu.setEnabled(self.mode == REGLAMENT)

    def input_key(self):
        '''Вывести диалоговое окно ввода идентификатора ключа и отправить запрос на ввод ключа'''
        key_id = self.keyIdDialog.exec()
        if key_id:
            self.send_request(input_key(key_id))
        
    def erase_key(self):
        '''Вывести диалоговое окно ввода идентификатора ключа и отправить запрос на стирание ключа'''
        key_id = self.keyIdDialog.exec()
        if key_id:
            self.send_request(erase_key(key_id))

    def output_key(self):
        '''Вывести диалоговое окно ввода идентификатора ключа и отправить запрос на вывод ключа'''
        key_id = self.keyIdDialog.exec()
        if key_id:
            self.send_request(output_key(key_id))
        
    def show_keys_number(self):
        '''Отправить запрос о количестве ключей'''
        self.send_request(ask_keys_number())
        
    def set_clock(self):
        '''Отправить запрос об установке времени'''
        self.send_request(set_clock())
        
    def generate_key(self):
        '''Вывести диалоговое окно ввода параметров ключа и отправить запрос на генерацию ключа'''
        key = self.keyParmsDialog.exec()
        if not key:
            return

        self.setCursor(QCursor(Qt.WaitCursor))

        self.send_request(set_mode(KEYGEN))
        time.sleep(10)
        self.send_request(set_clock())
        self.send_request(set_mode(REGLAMENT))
        time.sleep(10)
        self.send_request(gen_key(key))
        time.sleep(10)
        # Чтобы устройство реагировало на запросы, нужно переключить его в режим "Работа",
        # выдержать паузу 5-20 сек и снова установить время!
        self.send_request(set_mode(WORK))
        time.sleep(10)
        self.send_request(set_clock())
        
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
        self.send_request(set_admin_password(self.passwd, bytearray(passwd, 'utf-8')))
        self.passwd = bytearray(passwd, 'utf-8')
        return self.passwd

    def set_address(self):
        '''Установка IP-адресов интерфейсов изделия'''
        if self.addrDialog.exec():
            try:
                ip = self.addrDialog.addrLineEdit.text().split(':')[0]
                socket.inet_aton(ip)
                if self.addrDialog.typeComboBox.currentIndex() == 0:
                    # Установка IP-адреса интерфейса ЛВС изделия
                    self.send_request(set_address(INT_LAN, ip))
                    self.settings.beginGroup('Common')
                    self.settings.setValue('Host', self.addrDialog.addrLineEdit.text())
                    self.settings.endGroup()
                    QMessageBox.warning(self, 'Предупреждение', 'Для вступления изменений в силу, перезапустите программу управления')
                elif self.addrDialog.typeComboBox.currentIndex() == 1:
                    # Установка IP-адреса интерфейса ВВС изделия
                    self.send_request(set_address(INT_WAN, ip))
                else:
                    port = int(self.addrDialog.addrLineEdit.text().split(':')[1])
                    self.send_request(set_address(EXT_ASINC_SRV, ip, port))
            except socket.error:
                QMessageBox.critical(self, 'Ошибка', 'Введен неправильный ip-адрес')
            except (IndexError, ValueError):
                QMessageBox.critical(self, 'Ошибка', 'Не введен или введен неправильный номер порта')

    def reset_all(self):
        '''Отправить запрос на сброс устройства'''
        if QMessageBox.question(self, 'Внимание', 'После выполнения команды вся информация в запоминающем устройстве изделия будет стерта! Продолжить?') == QMessageBox.StandardButton.Yes:
            self.send_request(reset_all())
            time.sleep(2)
            self.send_request(set_clock())
            # Дефолтный пароль после сброса устройства
            self.passwd = bytearray('000000000000', 'utf-8')
            while not self.set_admin_password():
                pass

    def create_context_menu(self):
        self.resultsPlainTextEdit.menu = self.resultsPlainTextEdit.createStandardContextMenu()
        self.resultsPlainTextEdit.menu.addAction('Очистить все', self.resultsPlainTextEdit.clear)
        self.resultsPlainTextEdit.menu.exec_(QCursor.pos())
        
    def closeEvent(self, e):
        '''Сохранить геометрию, состояние главного окна и пароль'''
        self.settings.setValue('MainWindowGeometry', self.saveGeometry())
        self.settings.setValue('MainWindowState', self.saveState())
        # Если установлена опция "хранить пароль в настройках", сохранить его
        if self.settingsDialog.passwdPoliticComboBox.currentIndex():
            self.settings.setValue('Passwd', self.passwd)
        else:
            self.settings.setValue('Passwd', '')
        self.sock.close()
