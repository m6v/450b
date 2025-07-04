import configparser
import os
import sys

from PyQt5 import uic
from PyQt5.Qt import QDialog

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


class SettingsDialog(QDialog):
    """Диалоговое окно, отображающее настройки изделия и программы управления"""
    def __init__(self, parent, config):
        super().__init__(parent)
        uic.loadUi(os.path.join(CURRENT_DIR, 'SettingsDialog.ui'), self)

        self.config = config
        # Эту установку выполняем в конструкторе, иначе, если не открывать окно настроек,
        # дефолтное значение будет 0 и при закрытии основного окна, пароль не сохранится
        if self.config.get('general', 'passwd', fallback=''):
            self.passwdPoliticComboBox.setCurrentIndex(1)
        else:
            self.passwdPoliticComboBox.setCurrentIndex(0)

    def showEvent(self, e):
        self.devAddrLineEdit.setText(self.config.get('network', 'host', fallback='192.168.0.3'))
        self.devPortSpinBox.setValue(int(self.config.get('network', 'port', fallback='4660')))
        super().showEvent(e)
        self.update()
        
    def accept(self):
        self.config.set('network', 'host', self.devAddrLineEdit.text())
        self.config.set('network', 'port', str(self.devPortSpinBox.value()))
        super().accept()

    def get_passwd_store_politic(self):
        ''' Вернуть политику хранения паролей'''
        return self.passwdPoliticComboBox.currentIndex()
