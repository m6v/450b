TARGET = 450ctrl
RESOURCES = src/resources.py

srcdir = src

all: compile
	pyinstaller --onefile --windowed --add-data="src/*.ui:." --name $(TARGET) src/main.py
	test -f dist/config.ini || cp src/config.ini dist
	test -f dist/manual.pdf || cp src/manual.pdf dist

compile: $(RESOURCES)

src/%.py: src/%.qrc
	pyrcc5 $< -o $@

clean:
	rm -rf $(TARGET).spec build dist
