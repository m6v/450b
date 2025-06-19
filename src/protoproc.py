import binascii
from collections import namedtuple
from datetime import datetime
import socket
import struct

ADMIN_PASSWORD_LENGTH = 12

# Идентификаторы режимов
WORK = 0x00      # работа
CONTROL = 0x01   # контроль
REGLAMENT = 0x02 # регламент
KEYGEN = 0x03    # генерация ключей

MTCR_GETCLOCK = 0x00000001
MTCR_SETCLOCK = 0x00000002
MTCR_CREATEINTERFACE = 0x00000007
MTCR_SETASYNADDRESS = 0x00000010
MTCR_GETASYNADDRESS = 0x00000011
MTCR_GETCRC = 0x00000012
MTCR_GETFIRSTSTATUS = 0x00000013
MTCR_SET_ADMIN_PASSWORD = 0x00000014
MTCR_GET_HEALTH_STATUS = 0x00000015
MTCR_SETCHANNELMODE = 0x00000018
MTCR_ZASCOMMAND = 0x000000A0
MTCR_КМCOMMAND = 0x000000B0

MTCR = {MTCR_GETCLOCK: 'Запрос текущего времени',
        MTCR_SETCLOCK: 'Установка времени',
        MTCR_CREATEINTERFACE: 'Установка собственного IP-адреса интерфейса изделия',
        MTCR_SETASYNADDRESS: 'Установка адреса сервера асинхронных сообщений',
        MTCR_GETASYNADDRESS: 'Чтение адреса сервера для асинхронных сообщений от СКЗИ',
        MTCR_GETCRC: 'Запрос контрольной суммы ПО',
        MTCR_GETFIRSTSTATUS: 'Запрос статуса первоначального тестирования СКЗИ',
        MTCR_SET_ADMIN_PASSWORD: 'Смена административного пароля',
        MTCR_GET_HEALTH_STATUS: 'Проверка доступности и состояния СКЗИ',
        MTCR_SETCHANNELMODE: 'Установка/изменение режима работы СКЗИ',
        MTCR_ZASCOMMAND: 'Регламентные работы',
        MTCR_КМCOMMAND: 'Запрос общей статистики'
       }

ZAS_FL_COMMAND = 0x02
ZAS_REGIME_COMMAND = 0x03

ZAS_FL_ERASE_KEY = 0x02 # Стирание ключа в СКЗИ
ZAS_FL_RESET_ALL = 0x03 # Сброс изделия в начальное заводское состояние
ZAS_FL_INPUT_KEY = 0x05 # Ввод ключа в СКЗИ с внешнего ключевого носителя или из зоны хранения ключей
ZAS_FL_GET_KEYS = 0x06 # Запрос информации о ключах в рабочей области
ZAS_FL_GET_KEYS_STORAGE = 0x16 # Запрос информации о ключах в области хранения ключей
ZAS_FL_GENERATION_KEY_NOISE = 0x17 # Генерация ключа с заданными параметрами из шума (в особых условиях)
ZAS_FL_OUTPUT_KEY = 0x18 # Вывод ключа из СКЗИ на внешний ключевой носитель
ZAS_FL_NOISE_KEYS_NUMBER = 0x18 # Запрос информации о возможном количестве генерируемых ключей
ZAS_FL_ERASE_FIELD = 0x55 # Стирание ключей в зоне хранения ключей

MTCA_OK = 0x00000000
MTCA_OK_MODE = 0x00000001
MTCA_CLOCK = 0x00000001
MTCA_ASYNADDRESS = 0x00000007 # в документации не описана
MTCA_CRC = 0x00000008
MTCA_FIRSTSTATUS = 0x00000009
MTCA_HEALTH_STATUS = 0x0000000B
MTCA_ERROR_TIME = 0x00000080
MTCA_INVALIDPACKET = 0x00000083
MTCA_ERROR_INVAL = 0x00000084
MTCA_FATAL_ERROR =0x00000085
MTCA_ACCESSDENIED = 0x00000086
MTCA_ERROR_ZAS = 0x0000008A
MTCA_ZASCOMMAND = 0x000000A0

MTCA = {MTCA_OK: 'Успешное выполнение команды',
        MTCA_OK_MODE: 'Успешное выполнение команды установки режима',
        MTCA_CLOCK: 'Время в изделии',
        MTCA_ASYNADDRESS: 'Адрес для асинхронных сообщений',
        MTCA_CRC: 'Контрольная сумма ПО',
        MTCA_FIRSTSTATUS: 'Статус первоначального тестирования и версия ПО',
        MTCA_HEALTH_STATUS: 'Статус изделия',
        MTCA_ERROR_TIME: 'Ошибка при установке даты',
        MTCA_INVALIDPACKET: 'Непредусмотренный запрос',
        MTCA_ERROR_INVAL: 'Ошибки в параметрах',
        MTCA_FATAL_ERROR: 'Внутренняя ошибка',
        MTCA_ACCESSDENIED: 'Отказ в доступе',
        MTCA_ERROR_ZAS: 'Ошибка при работе с ключевым устройством',
        MTCA_ZASCOMMAND: 'Команда выполнена'
       }

FL_STATUS_OK = 0x00
FL_STATUS_GET_KEYS_OK = 0x08
FL_STATUS_UNDEFINED_COMMAND = 0x0A
FL_STATUS_KEY_ALREADY_IN_FLASH = 0x0B
FL_STATUS_WRITING_ERROR = 0x10
FL_STATUS_READING_ERROR = 0x11
FL_STATUS_NO_KEY = 0x16
FL_STATUS_ERASING_ERROR = 0x17
FL_STATUS_GET_KEYS_STORAGE_OK = 0x18
FL_STATUS_KEY_NOT_FOUND = 0x1B
FL_STATUS_INVALID_KEY = 0x20
FL_STATUS_NOISE_KEYS_NUMBER = 0x22

FL_STATUS = {FL_STATUS_OK: 'Успешное завершение операции СКЗИ',
             FL_STATUS_GET_KEYS_OK: 'Результат чтения состояния ключевых зон из области хранения ключей «Уступ»',
             FL_STATUS_UNDEFINED_COMMAND: 'СКЗИ получил непредусмотренный код команды работы с ключевым ЗУ',
             FL_STATUS_KEY_ALREADY_IN_FLASH: 'Попытка ввести ключ, который  уже есть',
             FL_STATUS_WRITING_ERROR: 'Ошибка при записи в ключевое ЗУ',
             FL_STATUS_READING_ERROR: 'Ошибка при чтении из ключевого ЗУ',
             FL_STATUS_ERASING_ERROR: 'Ошибка при стирании в ключевом ЗУ',
             FL_STATUS_INVALID_KEY: 'Ключ не соответствует требованиям',
             FL_STATUS_NO_KEY: 'Это не ключевая информация',
             FL_STATUS_KEY_NOT_FOUND: 'Поиск ключа завершился неудачей',
             FL_STATUS_GET_KEYS_STORAGE_OK: 'Результат чтения состояния ключевых зон из области хранения ключей «Уступ»',
             FL_STATUS_NOISE_KEYS_NUMBER: 'Возможное количество генерируемых ключей'
            }

KM_CMD_GET_PUBLIC_STATISTIC = 0xCB

ZAS_GET_TIME = 0xFE
RGM_STATUS_INCORRECT_KEY_ZONE = 0x03
RGM_STATUS_UNDEFINED_COMMAND = 0x08
RGM_STATUS_NO_CHENNEL_KEY = 0x0B
RGM_STATUS_NO_INIT_KEY = 0x0F
RGM_STATUS_NO_KEY = 0x04
RGM_STATUS_SELFTEST_ERROR = 0x09
RGM_STATUS_INACCESSIBLE_COMMAND = 0x0A
RGM_STATUS_UNDEFINED_PACKET = 0x08 # Одинаковый код с RGM_STATUS_UNDEFINED_COMMAND

RGM_STATUS = {ZAS_GET_TIME: 'Команда не выполнена, т.к. в изделии не установлено время',
              RGM_STATUS_INCORRECT_KEY_ZONE: 'Задан недопустимый идентификатор  ключа',
              RGM_STATUS_UNDEFINED_COMMAND: 'Получен непредусмотренный код команды',
              RGM_STATUS_NO_CHENNEL_KEY: 'Отсутствует сетевой  ключ',
              RGM_STATUS_NO_INIT_KEY: 'Отсутствует ключ инициализации',
              RGM_STATUS_NO_KEY: 'В носителе отсутствует указанный  ключ',
              RGM_STATUS_SELFTEST_ERROR: 'Команда не выполнена, т.к. была обнаружена ошибка при тестировании СКЗИ',
              RGM_STATUS_INACCESSIBLE_COMMAND: 'Команда не доступна в текущем режиме работы, перевести изделие в режим «Регламент»',
              RGM_STATUS_UNDEFINED_PACKET: 'СКЗИ получило непредусмотренный  пакет'
             }

KEYS_STORAGE = 0x0001
KEYS_RADIO = 0x0002

INT_LAN = 0x06 # интерфейс Ethernet ЛВС
INT_WAN = 0x09 # интерфейс Ethernet ВВС
INT_SLIP_L = 0x28 # интерфейс SLIP локальный
INT_SLIP_W = 0x31 # интерфейс SLIP внешний
EXT_ASINC_SRV = 0x00 # интерфейс сервера асинхронных сообщений

IFACES = {INT_LAN: 'Ethernet ЛВС',
          INT_WAN: 'Ethernet ВВС',
          EXT_ASINC_SRV: 'Сервер асинхронных сообщений'}

SPS_KEY_TTL_DAYS_1 = 0x31 # символ '1' в КОИ-7
SPS_KEY_TTL_DAYS_16 = 0x70 # символ 'П' в КОИ-7
SPS_KEY_TTL_MONTHS_1 = 0x71 # символ 'Я' в КОИ-7
SPS_KEY_TTL_MONTHS_3 = 0x73 # символ 'С' в КОИ-7
SPS_KEY_TTL_MONTHS_6 = 0x76 # символ 'Ж' в КОИ-7
SPS_KEY_TTL_YEARS_1 = 0x21 # символ '!' в КОИ-7

SPS_KEY_PERIOD_DAYS_1 = 0x31 # символ '1' в КОИ-7
SPS_KEY_PERIOD_DAYS_16 = 0x70 # символ 'П' в КОИ-7

KEY_ALGORITHM = {0xC5: 'Уступ', 0x1A: 'R-168'}

SPS_KEY_TTL = {SPS_KEY_TTL_DAYS_1: '1 день',
               SPS_KEY_TTL_DAYS_16: '16 дней',
               SPS_KEY_TTL_MONTHS_1: '1 месяц',
               SPS_KEY_TTL_MONTHS_3: '3 месяца',
               SPS_KEY_TTL_MONTHS_6: '6 месяцев',
               SPS_KEY_TTL_YEARS_1: '1 год'
              }

SPS_KEY_PERIOD = {SPS_KEY_PERIOD_DAYS_1: '1 день',
                  SPS_KEY_PERIOD_DAYS_16: '16 дней'
                 }
                  
Reply = namedtuple('Reply', ['code', 'length', 'body'])
Key = namedtuple('Key', ['id', 'zone', 'number', 'date', 'ttl', 'period'])

def hexdump(data: bytes):
    offset = 0
    while offset < len(data):
        chunk = data[offset:offset + 16]
        hex_values = ' '.join(format(byte, '02x') for byte in chunk)
        # В Python >= 3.8 можно использовать chunk.hex(sep=' ')
        ascii_values = ''.join(chr(byte) if 32 <= byte <= 126 else '.' for byte in chunk)
        print('{:08x}  {:<48}  |{}|'.format(offset, hex_values, ascii_values))
        offset += 16

# Определить запросы, не требующие аргументов
ask_asynaddress = lambda : struct.pack('>II', MTCR_GETASYNADDRESS, 0) # запросить адрес сервера асинхронных сообщений
ask_clock = lambda : struct.pack('>II', MTCR_GETCLOCK, 0) # запросить время
ask_crc = lambda : struct.pack('>II', MTCR_GETCRC, 0) # запросить контрольную сумму ПО
ask_first_status = lambda : struct.pack('>II', MTCR_GETFIRSTSTATUS, 0) # запросить статус первоначального тестирования
ask_mode = lambda : struct.pack('>II', MTCR_GET_HEALTH_STATUS, 0) # запросить состояние (режим) изделия
ask_keys_workspace = lambda : struct.pack('>IIBB', MTCR_ZASCOMMAND, 2, ZAS_FL_COMMAND, ZAS_FL_GET_KEYS) # запросить информацию о ключах в рабочей области
ask_keys_storage = lambda : struct.pack('>IIBB', MTCR_ZASCOMMAND, 2, ZAS_FL_COMMAND, ZAS_FL_GET_KEYS_STORAGE) # запросить информацию о ключах в области хранения ключей
ask_keys_number = lambda : struct.pack('>IIBB', MTCR_ZASCOMMAND, 2, ZAS_FL_COMMAND, ZAS_FL_NOISE_KEYS_NUMBER) # запросить информацию о возможном количестве генерируемых ключей
erase_field = lambda : struct.pack('>IIBB', MTCR_ZASCOMMAND, 2, ZAS_FL_COMMAND, ZAS_FL_ERASE_FIELD) # стереть зону хранения ключей ключевого устройства
reset_all = lambda : struct.pack('>IIBB', MTCR_ZASCOMMAND, 2, ZAS_FL_COMMAND, ZAS_FL_RESET_ALL) # сбросить устройство в начальное состояние

def input_key(key_id, key_zone=0):
    '''Ввод ключа с внешнего ключевого носителя'''
    return struct.pack('>IIBBB4s', MTCR_ZASCOMMAND, 7,
                                   ZAS_FL_COMMAND,
                                   ZAS_FL_INPUT_KEY,
                                   key_zone,
                                   key_id.encode())

def erase_key(key_id, key_zone=0):
    '''Стирание ключа'''
    return struct.pack('>IIBBB4s', MTCR_ZASCOMMAND, 7,
                                   ZAS_FL_COMMAND,
                                   ZAS_FL_ERASE_KEY,
                                   key_zone,
                                   key_id.encode())

def output_key(key_id, key_zone=0):
    '''Вывод ключа на внешний ключевой носитель'''
    return struct.pack('>IIBBB4s', MTCR_ZASCOMMAND, 7,
                                   ZAS_FL_COMMAND,
                                   ZAS_FL_OUTPUT_KEY,
                                   key_zone,
                                   key_id.encode())

def gen_key(key: Key):
    '''Генерация ключа'''
    if len(key.id) != 4:
        raise Exception('Идентификатор ключа не соответствует шаблону')
    # Параметры получатель (2 байта) и IP-адрес радиосредства (4 байта) в документации указаны, но не воспринимаются изделием
    return struct.pack('>IIBBB4s13s6sBB', MTCR_ZASCOMMAND, 28,
                                          ZAS_FL_COMMAND,
                                          ZAS_FL_GENERATION_KEY_NOISE,
                                          key.zone,
                                          key.id.encode(),
                                          str.encode(key.number),
                                          str.encode(key.date),
                                          key.ttl,
                                          key.period)

def set_admin_password(admin_passwd, new_passwd):
    '''Смена административного пароля'''
    # Если пароли меньше 12 символов, они автоматически дополняются нулями справа
    return struct.pack('>II12s12s', MTCR_SET_ADMIN_PASSWORD, 24, admin_passwd, new_passwd)

def set_address(iface_type, ip, port=0, mask='0.0.0.24', channel=0):
    '''Установка ip-адресов интерфейсов изделия и ip-адреса сервера асинхронных сообщений'''
    if iface_type in (INT_LAN, INT_WAN):
        # Установка собственного IP-адреса интерфейса изделия'''
        return struct.pack('>II4sBB', MTCR_CREATEINTERFACE, 6, socket.inet_aton(ip), iface_type, channel)
    if iface_type == EXT_ASINC_SRV:
        # Установка адреса сервера асинхронных сообщений'''
        return struct.pack('>II4s4sH', MTCR_SETASYNADDRESS, 10, socket.inet_aton(ip), socket.inet_aton(mask), port)
    raise Exception('Неизвестный тип интерфейса:', iface_type)

def set_clock():
    '''Установка времени'''
    now = datetime.now()
    return struct.pack('>IIBBBBBBB', MTCR_SETCLOCK, 7,
                                     now.second,
                                     now.minute,
                                     now.hour,
                                     now.weekday()+1,
                                     now.day,
                                     now.month,
                                     now.year-2000)

def set_mode(mode, channel=1):
    '''Установка/изменение режима работы'''
    '''
    NB! При переводе в режим контроля, возращается квитанция MTCA_FATAL_ERROR (0x0085),
    длина параметров 0х0004, параметры 0x1b000060 (то же значение, что и результат начального тестирования в квитанции MTCA_FIRSTSTATUS)
    '''
    if mode < 0 or mode > 3:
        raise Exception('Неправильный номер режима: %s' % mode)
    return struct.pack('>IIBB', MTCR_SETCHANNELMODE, 2,
                                channel,
                                mode)

def get_clock(reply, show_message):
    '''Обработка квитанции MTCA_CLOCK'''
    # В соответствии с протоколом код 0x00000001 имеют квитанции MTCA_CLOCK и MTCA_OK_MODE с длиной параметров 7 и 2 байта соответственно
    # После установки режима вместо квитанции MTCA_OK_MODE приходи MTCA_OK
    if reply.length == 7:
        S, M, H, w, d, m, y = struct.unpack('>BBBBBBB', reply.body)
        if y:
            dt = datetime(y+2000, m, d, H, M, S)
            show_message('Время в изделии:', dt)
        else:
            show_message('Время в изделии не установлено')
    else:
        show_message(MTCA[MTCA_OK_MODE])
        show_message('Номер канала:', reply.body[0])
        show_message('Статус изделия:', reply.body[1])

def get_crc(reply, show_message):
    '''Обработка квитанции MTCA_CRC о проверке целостности ПО'''
    show_message('Контрольная сумма ПО:', reply.body.hex())

def get_health_status(reply, show_message):
    '''Обработка квитанции MTCA_HEALTH_STATUS о текущем статусе изделия'''
    modes = ('работа (0x00)', 'контроль (0x01)', 'регламент (0x02)', 'генерация ключей (0x03)')
    show_message('Статус изделия:', modes[reply.body[0]])
    return {'mode': reply.body[0]}

def get_first_status(reply, show_message):
    '''Обработка квитанции MTCA_FIRSTSTATUS о статусе первоначального тестирования и версии ПО'''
    test_result, firmware_crc, firmware_major_version, firmware_minor_version = struct.unpack('>IIHH', reply.body[0:12])
    y, m, d, H, M = struct.unpack('>HBBBB', reply.body[12:18])
    dt = datetime(y, m, d, H, M)
    device_number = int.from_bytes(reply.body[18:22], byteorder='big')
    show_message('Результат начального тестирования:', hex(test_result))
    show_message('Прошитая контрольная сумма ПО:', hex(firmware_crc))
    show_message('Версия ПО: %s.%s' % (firmware_major_version, firmware_minor_version))
    show_message('Дата создания ПО:', dt)
    show_message('Номер изделия:', device_number)
    # Оставшаяся опциональная часть это комментарий (может не заканчиваться нулем или отсутствовать)

def get_error_zas(reply, show_message):
    '''Обработка квитанции MTCA_ERROR_ZAS об ошибке при управлении режимом'''
    if reply.body[0] == ZAS_REGIME_COMMAND:
        show_message(RGM_STATUS[reply.body[1]])
    elif reply.body[0] == ZAS_FL_COMMAND:
        show_message(FL_STATUS[reply.body[1]])
    else:
        show_message(MTCA[MTCA_ERROR_ZAS])

def get_zas_command(reply, show_message):
    '''Обработка квитанций MTCA_ZASCOMMAND об успешном завершении операции'''
    operation_type = reply.body[0]
    operation_result = reply.body[1]
    if operation_result == FL_STATUS_OK:
        show_message('Успешное завершение операции СКЗИ')

    elif operation_result == FL_STATUS_GET_KEYS_OK:
        # длина структуры SPS_KEY_STATUS
        SPS_KEY_STATUS_LEN = 37
        for i in range((reply.length-2)//SPS_KEY_STATUS_LEN):
            keys = ('key_zone', 'key_id', 'key_input_to_activation', 'key_type', 'key_ttl', 'key_period', 'key_algorithm', 'key_number', 'key_input_to_device', 'key_input_to_work')
            values = struct.unpack('>B4s3sBBBB13s6s6s', reply.body[2+i*SPS_KEY_STATUS_LEN:2+(i+1)*SPS_KEY_STATUS_LEN])
            SPS_KEY_STATUS = dict(zip(keys, values))
            show_message('Идентификатор ключа:', SPS_KEY_STATUS['key_id'].decode())
            show_message('Учетный номер ключа:', SPS_KEY_STATUS['key_number'].decode())
            show_message('Номер ключевой зоны:', SPS_KEY_STATUS['key_zone'])
            show_message('Тип ключа:', SPS_KEY_STATUS['key_type'])
            show_message('Алгоритм ключа:', KEY_ALGORITHM[SPS_KEY_STATUS['key_algorithm']])
            show_message('Дата ввода ключа в действие:', datetime(SPS_KEY_STATUS['key_input_to_activation'][2]+2000,
                                                                  SPS_KEY_STATUS['key_input_to_activation'][1],
                                                                  SPS_KEY_STATUS['key_input_to_activation'][0])
                                                                  )
            show_message('Срок действия ключа:', SPS_KEY_TTL[SPS_KEY_STATUS['key_ttl']])
            show_message('Период ключа:', SPS_KEY_TTL[SPS_KEY_STATUS['key_period']])
            show_message('Дата ввода ключа в изделие:', datetime(SPS_KEY_STATUS['key_input_to_device'][5]+2000,
                                                                 SPS_KEY_STATUS['key_input_to_device'][4],
                                                                 SPS_KEY_STATUS['key_input_to_device'][3],
                                                                 SPS_KEY_STATUS['key_input_to_device'][2],
                                                                 SPS_KEY_STATUS['key_input_to_device'][1],
                                                                 SPS_KEY_STATUS['key_input_to_device'][0])
                                                                 )
            
            show_message('Дата ввода ключа в работу:', datetime(SPS_KEY_STATUS['key_input_to_work'][5]+2000,
                                                                SPS_KEY_STATUS['key_input_to_work'][4],
                                                                SPS_KEY_STATUS['key_input_to_work'][3],
                                                                SPS_KEY_STATUS['key_input_to_work'][2],
                                                                SPS_KEY_STATUS['key_input_to_work'][1],
                                                                SPS_KEY_STATUS['key_input_to_work'][0])
                                                                )

    elif operation_result == FL_STATUS_GET_KEYS_STORAGE_OK:
        SPS_KEY_STORAGE_LEN = 9 # идентификатор ключа (4 байта) + дата (гмд) (3 байта) + срок действия 1 байт + период ключа 1 байт
        for i in range((reply.length-2)//SPS_KEY_STORAGE_LEN):
            key_id, key_input_to_action, key_ttl, key_period = struct.unpack('>4s3sBB', reply.body[2+i*SPS_KEY_STORAGE_LEN:2+(i+1)*SPS_KEY_STORAGE_LEN])
            show_message('Идентификатор ключа:', key_id.decode())
            show_message('Дата ввода ключа в работу:', datetime(key_input_to_action[2]+2000, 
                                                                key_input_to_action[1],
                                                                key_input_to_action[0]))
            show_message('Срок действия ключа:', SPS_KEY_TTL[key_ttl])
            show_message('Период ключа:', SPS_KEY_TTL[key_period])

    elif operation_result == FL_STATUS_NOISE_KEYS_NUMBER:
        show_message('Возможное количество ключей', int(reply.body[2:4].hex(), 16))

def get_fatal_error(reply, show_message):
    '''Обработка квитанции MTCA_FATAL_ERROR об общей внутренней ошибке'''
    # NB! При установке режима работы "Контроль" возвращает 4 байта параметров, что не является ошибкой,
    # поэтому сообщение об ошибке выводим только при нулевом количестве параметров
    if reply.length == 0:
        show_message(MTCA[reply.code])

def get_asyncaddress(reply, show_message):
    '''Обработка квитанции MTCA_ASYNADDRESS с адресом для асинхронных сообщений'''
    show_message('%s %s:%d' % (MTCA[reply.code], socket.inet_ntoa(reply.body[0:4]), int.from_bytes(reply.body[4:6], 'big')))

handlers = {MTCA_OK_MODE: get_clock,
            MTCA_CRC: get_crc,
            MTCA_HEALTH_STATUS: get_health_status,
            MTCA_FIRSTSTATUS: get_first_status,
            MTCA_ERROR_ZAS: get_error_zas,
            MTCA_ZASCOMMAND: get_zas_command,
            MTCA_FATAL_ERROR: get_fatal_error,
            MTCA_ASYNADDRESS: get_asyncaddress
            }

def parse_reply(data, show_message):
    '''Обработчик квитанций'''
    # Пропустить первые 8 байт (2 - идентификатор управляющей программы, 2 - порядковый номер инструкции, 2 - признак изделия, 2 - номер изделия)
    reply = Reply(*struct.unpack('>II', data[8:16]), data[16:])
    try:
        # Вызвать обработчик квитанции с кодом reply.code и передать ему квитанцию и функцию обратного вызова для печати результатов
        return handlers[reply.code](reply, show_message)
    except KeyError:
        # Обработка квитанций без параметров, заключающаяся в выводе сообщения в зависимости от кода квитанции
        if reply.code in (MTCA_OK, MTCA_INVALIDPACKET, MTCA_ERROR_INVAL, MTCA_ACCESSDENIED):
            show_message(MTCA[reply.code])
        else:
            show_message('Неизвестная квитанция с кодом', reply.code)
