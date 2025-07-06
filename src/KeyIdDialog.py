import os

from PyQt5 import uic
from PyQt5.Qt import QDialog, QRegularExpression, QRegularExpressionValidator, QStyle

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


class KeyIdDialog(QDialog):
    """Диалоговое окно, отображающее поле ввода идентификатора ключа"""
    def __init__(self, parent):
        super().__init__(parent)
        uic.loadUi(os.path.join(CURRENT_DIR, 'KeyIdDialog.ui'), self)

        validator = QRegularExpressionValidator(QRegularExpression("[a-zA-Z0-9]+"))
        self.keyIdlineEdit.setValidator(validator)

        icon = self.style().standardIcon(getattr(QStyle, 'SP_DialogOkButton'))
        self.okPushButton.setIcon(icon)
        icon = self.style().standardIcon(getattr(QStyle, 'SP_DialogCancelButton'))
        self.cancelPushButton.setIcon(icon)

        self.keyIdlineEdit.textChanged[str].connect(self.key_id_changed)

    def exec(self):
        self.keyIdlineEdit.setText('')
        # Возвратить идентификатор ключа или False, если была нажата клавиша "Отмена"
        return self.keyIdlineEdit.text() if super().exec() else False

    def key_id_changed(self, text):
        self.okPushButton.setEnabled(len(text) == 4)
