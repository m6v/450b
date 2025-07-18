import os
import random

from PyQt5 import uic
from PyQt5.Qt import QDialog, QRegularExpression, QRegularExpressionValidator, QDateTime, QStyle

import protoproc

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


class KeyParmsDialog(QDialog):
    """Диалоговое окно, отображающее поля с параметрами ключа"""
    def __init__(self, parent):
        super().__init__(parent)
        uic.loadUi(os.path.join(CURRENT_DIR, 'KeyParmsDialog.ui'), self)

        validator = QRegularExpressionValidator(QRegularExpression('[A-Z,a-z,0-9]+'))
        self.keyIdLineEdit.setValidator(validator)

        icon = self.style().standardIcon(getattr(QStyle, 'SP_DialogOkButton'))
        self.okPushButton.setIcon(icon)
        icon = self.style().standardIcon(getattr(QStyle, 'SP_DialogCancelButton'))
        self.cancelPushButton.setIcon(icon)

        for value in protoproc.SPS_KEY_TTL:
            self.durationComboBox.addItem(protoproc.SPS_KEY_TTL[value])
        self.durationComboBox.setCurrentIndex(len(protoproc.SPS_KEY_TTL[value]))
        for value in protoproc.SPS_KEY_PERIOD:
            self.periodComboBox.addItem(protoproc.SPS_KEY_PERIOD[value])
        self.periodComboBox.setCurrentIndex(0)

        self.keyIdLineEdit.textChanged[str].connect(self.key_id_changed)

    def key_id_changed(self, text):
        if len(text) == 4:
            self.okPushButton.setEnabled(True)
        else:
            self.okPushButton.setEnabled(False)

    def exec(self):
        self.keyNumberLineEdit.setText(''.join((random.choice('0123456789') for i in range(11))) + '00')
        self.keyIdLineEdit.setText('')
        self.dateEdit.setDateTime(QDateTime.currentDateTime())
        if super().exec():
            date = self.dateEdit.date()
            key = protoproc.Key(self.keyIdLineEdit.text(),
                                0,
                                self.keyNumberLineEdit.text(),
                                date.toString('yyMMdd'),
                                list(filter(lambda x: protoproc.SPS_KEY_TTL[x] == self.durationComboBox.currentText(), protoproc.SPS_KEY_TTL))[0],
                                list(filter(lambda x: protoproc.SPS_KEY_PERIOD[x] == self.periodComboBox.currentText(), protoproc.SPS_KEY_PERIOD))[0]
                                )
            return key

    def showEvent(self, e):
        super().showEvent(e)
        self.update()
