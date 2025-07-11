TARGET = 450ctrl
RESOURCES = src/resources.py

srcdir = src

all: compile src/*.py src/*.ui
	pyinstaller --onefile --windowed --add-data="src/*.ui:." --name $(TARGET) src/main.py
	test -f dist/config.ini || cp src/config.ini dist
	test -f dist/manual.pdf || cp src/manual.pdf dist

compile: $(RESOURCES)

# $@ - имя цели ($(RESOURCES))
# $< - имя первого переквизита (prerequisite, зависимость) (src/resources.qrc)
# $^ - список всех пререквизитов (разделенных пробелами)
$(RESOURCES): src/resources.qrc src/*.ui icons/*.png
	pyrcc5 src/resources.qrc -o $@

clean:
	rm -rf $(TARGET).spec build dist
	rm -rf src/__pycache__
