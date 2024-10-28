import ipaddress
import os

from PyQt5 import uic
from PyQt5.Qt import QDialog, QRegularExpression, QRegularExpressionValidator, QStyle

from protoproc import *

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

class AddrDialog(QDialog):
    """Диалоговое окно, отображающее тип и адрес интерфейса"""
    # TODO Сделать возврат ip и port
    def __init__(self, parent):
        super().__init__(parent)
        uic.loadUi(os.path.join(CURRENT_DIR, 'AddrDialog.ui'), self)
        
        validator = QRegularExpressionValidator(QRegularExpression("[0-9\.\:]+"))
        self.addrLineEdit.setValidator(validator)
        
        icon = self.style().standardIcon(getattr(QStyle, 'SP_DialogOkButton'))
        self.okPushButton.setIcon(icon)
        icon = self.style().standardIcon(getattr(QStyle, 'SP_DialogCancelButton'))
        self.cancelPushButton.setIcon(icon)
        
        for item in IFACES:
            self.typeComboBox.addItem(IFACES[item])
        
        self.typeComboBox.currentIndexChanged.connect(self.iface_type_changed)
        self.addrLineEdit.textChanged[str].connect(self.addr_changed)
        
    def iface_type_changed(self, index):
        self.addrLineEdit.setText('')
        if index == 2:
            self.addrLabel.setText('Адрес:порт')
        else:
            self.addrLabel.setText('Адрес')
    
    def addr_changed(self, text):
        # Проверить валидность введенного адреса и установить состояние кнопки "Ок"
        try:
            if ipaddress.ip_address(text.split(':')[0]):
                self.okPushButton.setEnabled(True)
        except:
            self.okPushButton.setEnabled(False)


    def showEvent(self, e):
        self.addrLineEdit.setText('')
        super().showEvent(e)
        self.update()
