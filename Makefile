TARGET = 450ctrl

all: pyrcc
	pyinstaller --onefile --add-data="src/*.ui:." --name $(TARGET) src/main.py
	# test -f dist/config.ini || cp src/config.ini dist
	test -f dist/manual.pdf || cp src/manual.pdf dist
pyrcc:
	# Компиляция ресурсов
	cd src; pyrcc5 resources.qrc -o resources.py
clean:
	rm -rf $(TARGET).spec build dist
