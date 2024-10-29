import os

from PyQt5 import uic
from PyQt5.Qt import QDialog, QLineEdit, QRegularExpression, QRegularExpressionValidator, QIcon, QStyle

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

class PasswdDialog(QDialog):
    """Диалоговое окно, отображающее поле ввода пароля изделия"""
    def __init__(self, parent):
        super().__init__(parent)
        uic.loadUi(os.path.join(CURRENT_DIR, 'PasswdDialog.ui'), self)
        
        validator = QRegularExpressionValidator(QRegularExpression("[0-9]+"))
        self.passwdLineEdit.setValidator(validator)
        
        self.iconShow = QIcon('../icons/view.png')
        self.iconHide = QIcon('../icons/hide.png')
        self.showPassAction = self.passwdLineEdit.addAction(self.iconShow, QLineEdit.TrailingPosition)
        self.showPassAction.setCheckable(True)
        self.showPassAction.toggled.connect(self.toggle_password_visibility)
        
        # Здесь не используем, т.к. дублирует надпись над полем ввода
        # self.passwdLineEdit.setPlaceholderText('Введите пароль...')
        
        # названия см.: https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QStyle.htm
        icon = self.style().standardIcon(getattr(QStyle, 'SP_DialogOkButton'))
        self.okPushButton.setIcon(icon)
        icon = self.style().standardIcon(getattr(QStyle, 'SP_DialogCancelButton'))
        self.cancelPushButton.setIcon(icon)
       
        self.passwdLineEdit.textChanged[str].connect(self.passwd_changed)

    def exec(self, label_text='Введите пароль изделия (12 симв.)'):
        self.passwdLabel.setText(label_text)
        self.passwdLineEdit.setText('')
        # Возвратить пароль или False, если была нажата клавиша "Отмена"
        return self.passwdLineEdit.text() if super().exec() else False

    def passwd_changed(self, text):
        # Если пароль меньше 12 символов, то в запросе (set_admin_password) он дополняется нулями справа
        self.okPushButton.setEnabled(len(text) != 0)

    def toggle_password_visibility(self, show):
        if show:
            self.passwdLineEdit.setEchoMode(QLineEdit.Normal)
            self.showPassAction.setIcon(self.iconHide)
        else:
            self.passwdLineEdit.setEchoMode(QLineEdit.Password)
            self.showPassAction.setIcon(self.iconShow)

    def result(self):
        return self.passwdLineEdit.text()
