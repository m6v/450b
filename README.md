# Использование Pyinstaller

[Как создать exe файл для Python кода с помощью PyInstaller](https://pythonru.com/biblioteki/pyinstaller)
[Разработка десктопных приложений. Python. Pyinstaller](https://docs.astralinux.ru/latest/desktop/python/pyinstaller)

PyInstaller — инструмент для упаковки Python-приложений в standalone-исполняемые файлы, включающий интерпретатор Python и все зависимости. 

## Установка Pyinstaller

В зависимости от дистрибутива Pyinstaller устанавливается с помощью пакетного менеджера или pip

```
sudo apt install python3-pyinstaller
pip install pyinstaller
```

Для корректной работы Pyinstaller, в ALSE 1.8 необходимо установить пакет `pyinstaller-hooks-contrib` из пакетного менеджера pip:

```
sudo apt install python3-pip
sudo pip3 install --break-system-packages pyinstaller-hooks-contrib
```

## Создание исполняемого файла

Для создания исполняемого файла достаточно выполнить команду

```
pyinstaller <имя_файла>.py
```

В результате будет созданы:

`*.spec` – файл спецификации (используется для ускорения будущих сборок приложения, связи файлов данных с приложением, для включения `.dll` и `.so` файлов, добавление в исполняемый файл параметров `runtime` Python);

`build/` – директория с метаданными для сборки исполняемого файла;

`dist/` – директория, содержащая все зависимости и исполняемый файл.

## Параметры командной строки 

Сборку приложения можно настроить с помощью параметров командной строки:

`--name` – изменение имени исполняемого файла (по умолчанию, такое же, как у сценария);

`--onefile` – создание только исполняемого файла (по умолчанию, папка с зависимостями и исполняемый файл);

`--hidden-import` – перечисление импортов, которые PyInstaller не смог обнаружить автоматически;

`--add-data` – добавление в сборку файлов данных;

`--add-binary` – добавление в сборку бинарных файлов;

`--exclude-module` – исключение модулей из исполняемого файла;

`--add-data` – добавление дополнительных файлов;

`--windowed` – скрытие консоли (актуально для GUI-приложений);

`--key` – ключ шифрования AES256 для обфусцирования байт-кода Python с помощью шифрования.

## Конфигурационный .spec файл

Файл .spec — это конфигурационный файл, который PyInstaller создаёт при первой сборке.

Чтобы создать spec-файл до первой сборки, необходимо в каталоге проекта выполнить команду

```
pyi-makespec my_app
```

Для более тонкой настройки процесса сборки spec-файл можно редактировать,например:

```
-*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['my_app.py'],
    pathex=['/path/to/your/project'], # путь к каталогу проекта
    binaries=[],
    datas=[('images/*.png', 'images')],  # файлы, которые нужно загрузить для работы приложения
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MyAwesomeApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # скрыть консоль
    icon='app_icon.ico',  # иконка
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MyAwesomeApp', # имя исполняемого файла
)
```

Чтобы собрать проект с использованием .spec файла, необходимо выполнить команду

```
pyinstaller my_app.spec
```

## Добавление файлов с данными, которые будут использоваться исполняемым файлом

Для добавления файлов с данными в один бандл с исполняемым файлом, используется параметр --add-data, который можно применить необходимое количество раз.

Синтаксис add-data:

```
add-data <source;destination> — Windows.
add-data <source:destination> — Linux.
``

Открыв spec-файл, можно увидеть раздел datas, в котором указывается список datas в котором указываются файлы, которые нужно загрузить для работы приложения (изображения, музыка/звуки, шрифты). Datas — это список кортежей. Каждый кортеж имеет два элемента строкового типа:
первый — путь до файла, который нужно загрузить, второй указывает имя папки для хранения файла во время выполнения программы ('.' — означает, что файл будет помещен во временную папку без подкаталога).

## Ограничения

У PyInstaller есть ограничения. Он работает с Python 3.5–3.9. Поддерживает создание исполняемых файлов для разных операционных систем, но не умеет выполнять кросскомпиляцию, т. е. необходимо генерировать исполняемый файл для каждой ОС отдельно. Более того, исполняемый файл зависит от пользовательского glibc, т. е. необходимо генерировать исполняемый файл для самой старой версии каждой ОС.

PyInstaller знает о многих Python-пакетах и умеет их учитывать при сборке исполняемого файла. Но не о всех. Например, фреймворк uvicorn практически весь нужно явно импортировать в файл, к которому будет применена команда pyinstaller. Полный список поддерживаемых из коробки пакетов можно посмотреть [здесь](https://github.com/pyinstaller/pyinstaller/wiki/Supported-Packages).


## Описание особенностей, связанных с изменениями каталогов

При запуске приложения PyInstaller распаковывает данные во временную папку и сохраняет путь к ней в переменной среды _MEIPASS.

Для определения путей к дополнительным файлам можно использовать следующую функцию

```
import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
```
Функция resource_path проверяет создана ли временная папка, и если да, то возвращает путь к ней для дальнейшей загрузки файлов. В противном случае (например, если запустить код через интерпретатор) функция вернет тот путь, который в неё передали.

[Bundling data files with PyInstaller](https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile)
[Add configuration file outside PyInstaller --onefile EXE file into dist directory](https://stackoverflow.com/questions/47850064/add-configuration-file-outside-pyinstaller-onefile-exe-file-into-dist-director/59415662)

## Особенности запуска программы с правами суперпользователя
1) Для запуска программы с правами root в ОС Astra Linux используется программа fly-su. В других ОС GNU/Linux может использоваться программа pkexec, которая является частью PolicyKit и позволяет более точно распределять права. Перед использованием pkexec необходимо создать в каталоге /usr/share/polkit-1/actions файл *.policy в котором должен быть указан путь к исполняемому файлу!
2) Запуск "упакованного" исполняемого файла python с помощью pkexec будет неудачным, т.к. каждый раз распаковка происходит в разные подкаталоги /tmp и их заранее невозможно указать в файле политик PolicyKit.
3) Для просмотра отладочной информации в stdout запускать программу, используя sudo.
4) В функции set_address(self), выполняющей установку IP-адресов интерфейсов изделия не понятно как устанавливать маску сети и порт для внутреннего интерфейса управления, т.к. в протоколе предусмотрена только установка IP-адреса.

## Запуск привилегированных приложений с pkexec

Для приложений, которым требуется повышение привилегий вместо механизма sudo можно использовать pkexec, который  является частью PolicyKit.

Для этого достаточно только описать разрешения приложения в отдельном xml-конфиге.

Например, для программы xed создадим файл ```/usr/share/polkit-1/actions/org.gnome.xed.policy```

```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN" "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>

    <vendor>The Linux Mint Russian Community</vendor>
    <vendor_url>https://linuxmint.com.ru/</vendor_url>
    <icon_name>xed</icon_name>
    <action id="org.gnome.xed">

        <description gettext-domain="xed">Run xed as root</description>
        <message gettext-domain="xed">Authentication is required to run the Xed Editor as root</message>
        <defaults>
            <allow_any>auth_admin</allow_any>
            <allow_inactive>auth_admin</allow_inactive>
            <allow_active>auth_admin</allow_active>
        </defaults>
        <annotate key="org.freedesktop.policykit.exec.path">/usr/bin/xed</annotate>
        <annotate key="org.freedesktop.policykit.exec.allow_gui">true</annotate>

    </action>

</policyconfig>
```

Краткое пояснение по значениям полей блока <policyconfig>

**vendor** - название разработчика программного обеспечения (вендора) или имя проекта (необязательный элемент).

**vendor_url** - URL проекта или вендора (необязательный элемент).

**icon_name** - имя значка, представляющего проект или вендора (необязательный элемент).

**action** - это элемент, который содержит внутри себя другие элементы (в открывающем тэге action обязательно указывается идентификатор действия - id, который передается по шине D-Bus).

Элементов action в одном файле может быть несколько. Внутри элемента action можно найти:

**description** - краткое описание действия, понятное человеку. Элементов description может быть несколько, например, для разных языков.

**message** - понятное оператору сообщение, которое будет появляться в окне запроса авторизации, если она потребуется. Элементов message может быть несколько, например, для разных языков.

**defaults** - этот элемент определяет необходимость и тип авторизации по умолчанию для действия, указанного в элементе action.
Здесь возможно использование трех необязательных элементов, определяющих неявные разрешения для клиентов, работающих в локальной консоли:

**allow_any** - для любых клиентов;

**allow_inactive** - для клиентов неактивных сеансов;

**allow_active** - для клиентов активных сеансов;

Элементы allow_any, allow_inactive и allow_active могут содержать следующие значения:
no - действие не разрешается;
yes - действие разрешается;
auth_self - требуется аутентификация от имени владельца сеанса;
auth_admin - требуется аутентификация от имени суперпользователя, что является более серьезным ограничением, чем предыдущий вариант;
auth_self_keep - то же, что и auth_self, но разрешение имеет силу в течение некоторого небольшого периода времени (например, пять минут);
auth_admin_keep - то же, что и auth_admin, но разрешение имеет силу в течение некоторого небольшого периода времени (например, пять минут);

Если не требуется настраивать тонкие политики, то для разных приложений в данном шаблоне изменяются только строки action id, description, message и exec.path
Чтобы разрешить пользователю запускать данный экземпляр программы без запроса пароля задать поле <allow_active>yes</allow_active>. 
