TARGET = 450ctrl

all:
	# Опции --hidden-import PyQt5.QtCore --hidden-import PyQt5.QtGui --hidden-import PyQt5.QtWidgets оказались не нужны
	pyinstaller --onefile --add-data="src/*.ui:." --add-data="icons/*.png:icons" --name $(TARGET) src/main.py
	test -f dist/config.ini || cp src/config.ini dist
	cp src/manual.pdf dist
clean:
	rm -rf $(TARGET).spec build dist
