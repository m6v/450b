import os

from PyQt5 import uic
from PyQt5.Qt import QDialog, QSettings

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_FILE = os.path.join(CURRENT_DIR, 'settings.ini')

# Password editing field, with Show/Hide toggle см.: https://www.pythonguis.com/widgets/passwordedit/

class SettingsDialog(QDialog):
    """Диалоговое окно, отображающее настройки изделия и программы управления"""
    def __init__(self, parent):
        super().__init__(parent)
        uic.loadUi(os.path.join(CURRENT_DIR, 'SettingsDialog.ui'), self)
        
        self.settings = QSettings(SETTINGS_FILE, QSettings.IniFormat)
        # Эту установку выполняем в конструкторе, иначе если не открывать окно настроек,
        # дефолтное значение будет 0 и при закрытии основного окна, пароль не сохранится
        if self.settings.value('Passwd'):
            self.passwdPoliticComboBox.setCurrentIndex(1)
        else:
            self.passwdPoliticComboBox.setCurrentIndex(0)

    def showEvent(self, e):
        self.settings.beginGroup('Common')
        self.devAddrLineEdit.setText(self.settings.value('Host', '192.168.0.3'))
        self.devPortSpinBox.setValue(int(self.settings.value('Port', '4660')))
        self.settings.endGroup()
        
        super().showEvent(e)
        self.update()
        
    def accept(self):
        self.settings.beginGroup('Common')
        self.settings.setValue('Host', self.devAddrLineEdit.text())
        self.settings.setValue('Port', self.devPortSpinBox.value())
        self.settings.endGroup()
        self.settings.sync()

        super().accept()

