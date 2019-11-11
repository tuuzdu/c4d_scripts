#!/usr/bin/python
# -*- coding: utf-8  -*-

import c4d
from c4d import Ttexture
from c4d import gui, documents
import os
import math
import errno
import struct
import binascii
import ConfigParser

#по поводу импорта конфиг парсера:
#https://stackoverflow.com/questions/5055042/whats-the-best-practice-using-a-settings-file-in-python
#https://wiki.python.org/moin/ConfigParserExamples

# This number is the unique ID that is assigned to the plugin. Every
# plugin must have a unique ID which can be obtained from
# http://plugincafe.com/forum/developer.asp
PLUGIN_ID = 1072398 # пока что это ненастоящий ID

# This structure will contain all of our resource symbols that we
# use in the TaskListDialog. Prevents pollution of the global scope.
# We can use type() to create a new type from a dictionary which will
# allow us to use attribute-access instead of bracket syntax.
res = type('res', (), dict(
    # ID of the text that displays the active document's name.
    TEXT_DOCINFO = 1001, # Подпись. Сведения об открытом документе
    TEXT_OUTPUT_FOLDER = 1002, # Подпись. Путь до целевой папки
    TEXT_PREFIX = 1003, # Подпись. Префиксом объектов
    TEXT_OBJECT_COUNT = 1004, # Подпись. Количеством объектов
    TEXT_SCALE_GLOBAL = 1005, # Подпись. Глобальный пространственный масштаб
    TEXT_SCALE_PARTIAL= 1006, # Подпись. Частичный масштабом по x, y, z
    TEXT_ROTATION = 1007, # Подпись. Поворот в градусах
    TEXT_HEIGHT_OFFSET= 1008, # Подпись. Сдвиг по высоте
    TEXT_POINTS_FREQ = 1009, # Подпись. Частота точек
    TEXT_COLORS_FREQ = 1010, # Подпись. Частота цветов
    TEXT_TEMPLATE_PATH= 1011, # Подпись. Выбор файла шаблона
    TEXT_LAT_LON_PARTIAL=1012, # Подпись. Точка GPS
    TEXT_MAX_VELOCITY = 1013, # Подпись. Максимальная скорость
    TEXT_MIN_DISTANCE = 1014, # Подпись. Минимальная дистанция
    TEXT_ANIMATION_ID = 1015, # Подпись. ID анимации
    TEXT_START_COLOR = 1016, # Подпись. Цвет светодиодов на предстартовой подготовке
    TEXT_CFG_FILE = 1017, # Подпись. Конфигурационный файл
    TEXT_TIME = 1018, # Подпись. Время
    
    
    # This is the ID for the group that contains the task widgets.
    GROUP_TASKS = 2000,

    BUTTON_OUTPUT_FOLDER = 3000, # Идентификатор кнопки для открытия целевой папки для скриптов
    BUTTON_TEMPLATE_PATH = 3001, # Идентификатор кнопки для выбора шаблона c4d_animation.lua
    BUTTON_GENERATE = 3002, # Идентификатор кнопки для запуска генерации скриптов
    BUTTON_LOAD_CONFIG = 3003, # Кнопка загрузки конфигурации
    BUTTON_SAVE_CONFIG= 3004, # Кнопка сохранения конфигурации
    
    EDIT_OUTPUT_FOLDER = 4000, # Идентификатор текстового поля, в котором хранится путь до целевой папки
    EDIT_PREFIX = 4001, # Идентификатор текстового поля с префиксом объектов
    EDIT_OBJECT_COUNT = 4002, # Идентификатор текстового поля с количеством объектов
    EDIT_SCALE_GLOBAL = 4003, # Текстовое поле с глобальным пространственным масштабом
    EDIT_SCALE_X= 4004, # Текстовое поле с масштабом по x
    EDIT_SCALE_Y= 4005, # Текстовое поле с масштабом по y
    EDIT_SCALE_Z= 4006, # Текстовое поле с масштабом по z
    EDIT_ROTATION = 4007, # Текстовое поле, редактирующее поворот в градусах
    EDIT_HEIGHT_OFFSET= 4008, # Текстовое поле. Сдвиг по высоте
    EDIT_POINTS_FREQ = 4009, # Текстовое поле с частотой точек в герцах
    EDIT_COLORS_FREQ = 4010, # Текстовое поле с частотой цветов в герцах
    EDIT_TEMPLATE_PATH = 4011, # Идентификатор текстового поля, в котором хранится путь до шаблона c4d_animation.lua
    EDIT_LAT = 4012,
    EDIT_LON = 4013,
    EDIT_MAX_VELOCITY = 4014, # Максимальная скорость при проверке объектов
    EDIT_MIN_DISTANCE = 4015, # Минимальная дистанция между дронами при проверке
    EDIT_ANIMATION_ID = 4016, # ID анимации
    EDIT_START_COLOR = 4017, # Стартовый цвет светодиодов
    EDIT_TIME_START = 4018, # Время начала
    EDIT_TIME_END = 4019, # Время конца
    
    COLOR_RED = 5000,
    COLOR_ORANGE = 5001,
    COLOR_YELLOW = 5002,
    COLOR_CYAN = 5003,
    COLOR_PURPLE = 5004,
    
    # строковые константы
    STR_CFG_SECTION = "PioneerCapture",
    STR_CFG_START_COLOR = "StartColor",
    STR_CFG_ANIMATION_ID = "AnimationId",
    STR_CFG_POINTS_FREQ = "PointsFreq",
    STR_CFG_COLORS_FREQ = "ColorsFreq",
    STR_CFG_SCALE_X = "ScaleX",
    STR_CFG_SCALE_Y = "ScaleY",
    STR_CFG_SCALE_Z = "ScaleZ",
    STR_CFG_LAT = "Lat",
    STR_CFG_LON = "Lon",
    STR_CFG_PREFIX = "Prefix",
    STR_CFG_HEIGHT_OFFSET = "HeightOffset",
    STR_CFG_OBJECT_COUNT = "ObjectCount",
    STR_CFG_MAX_VELOCITY = "MaxVelocity",
    STR_CFG_MIN_DISTANCE = "MinDistance",
    STR_CFG_ROTATION = "Rotation",
    STR_CFG_TEMPLATE_PATH = "TemplatePath",
    STR_CFG_OUTPUT_FOLDER = "OutputFolder",

))

# класс необходим для создания GUI-окна
# см. пример:
# https://github.com/PluginCafe/py-cinema4dsdk/blob/master/gui/task-list.pyp
# https://developers.maxon.net/docs/Cinema4DPythonSDK/html/modules/c4d.gui/GeDialog/index.html
# для работы с файловой системой:
# https://developers.maxon.net/docs/Cinema4DPythonSDK/html/modules/c4d.storage/index.html

def RaiseMessage(message):
    gui.MessageDialog(message)

def RaiseErrorMessage(message):
    gui.MessageDialog(message, type=c4d.GEMB_ICONEXCLAMATION)

class GenerationError(Exception):
    def __init__(self, console=None, dialog=None):
        if console is not None:
            print(console)
        else:
            print('Error occured.')
        print('\nGeneration stopped.')
        if dialog is not None:
            RaiseErrorMessage(dialog + '\n\nСheck console for more details.\nMain menu->Script->Console')

class PioneerCaptureDialog(c4d.gui.GeDialog):
    def __init__(self):
        self.current_doc = c4d.documents.GetActiveDocument()
        self.output_folder = None # по умолчанию папка вывода скриптов не выбрана (можно исправить на пользовательские опции)

    def Refresh(self, flush=True, force=False, initial=False, reload_=False):
        self.current_doc = c4d.documents.GetActiveDocument()
        title_text = "Project: %s" % self.current_doc.GetDocumentName()
        self.SetString(res.TEXT_DOCINFO, title_text)

    def getColorName(self, color_id):
        if color_id == res.COLOR_RED:
            return "red"
        if color_id == res.COLOR_ORANGE:
            return "orange"
        if color_id == res.COLOR_YELLOW:
            return "yellow"
        if color_id == res.COLOR_CYAN:
            return "cyan"
        if color_id == res.COLOR_PURPLE:
            return "purple"

    def getColorId(self, color):
        if color == "red":
            return res.COLOR_RED
        if color == "orange":
            return res.COLOR_ORANGE
        if color == "yellow":
            return res.COLOR_YELLOW
        if color == "cyan":
            return res.COLOR_CYAN
        if color == "purple":
            return res.COLOR_PURPLE

    def getColorHue(self, color):
        if color == "red":
            return 0
        if color == "orange":
            return 24
        if color == "yellow":
            return 60
        if color == "cyan":
            return 180
        if color == "purple":
            return 300

    # функция для сохранения настроек в конфигурационном файле
    def saveConfig(self):
        filename = c4d.storage.LoadDialog(title="Choose template file", flags=c4d.FILESELECT_SAVE, def_path=self.plugin.module_path, def_file="config.ini")
        if filename is None:
            return
        cfgfile = open(filename, 'w')

        # add the settings to the structure of the file, and lets write it out...
        Config = ConfigParser.ConfigParser()
        Config.add_section(res.STR_CFG_SECTION)
        
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_START_COLOR, self.getColorName(self.GetLong(res.EDIT_START_COLOR)))
        # Config.set(res.STR_CFG_SECTION, res.STR_CFG_ANIMATION_ID, self.GetInt32(res.EDIT_ANIMATION_ID))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_POINTS_FREQ, self.GetString(res.EDIT_POINTS_FREQ))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_COLORS_FREQ, self.GetString(res.EDIT_COLORS_FREQ))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_SCALE_X, self.GetString(res.EDIT_SCALE_X))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_SCALE_Y, self.GetString(res.EDIT_SCALE_Y))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_SCALE_Z, self.GetString(res.EDIT_SCALE_Z))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_LAT, self.GetString(res.EDIT_LAT))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_LON, self.GetString(res.EDIT_LON))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_PREFIX, self.GetString(res.EDIT_PREFIX))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_HEIGHT_OFFSET, self.GetString(res.EDIT_HEIGHT_OFFSET))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_OBJECT_COUNT, self.GetString(res.EDIT_OBJECT_COUNT))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_MAX_VELOCITY, self.GetString(res.EDIT_MAX_VELOCITY))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_MIN_DISTANCE, self.GetString(res.EDIT_MIN_DISTANCE))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_ROTATION, self.GetString(res.EDIT_ROTATION))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_TEMPLATE_PATH, self.GetString(res.EDIT_TEMPLATE_PATH))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_OUTPUT_FOLDER, self.GetString(res.EDIT_OUTPUT_FOLDER))
        Config.write(cfgfile)
        cfgfile.close()

    def loadConfigError(self, field, e):
        return str(e)
        if e == 'NoOptionError':
            return 'No field \'{}\'\n'.format(field)
        elif e == 'TypeError' or e == 'ValueError':
            return 'Field \'{}\' has invalid value\n'.format(field)
        else:
            return '{}\n'.format(str(e))

    # функция для загрузки настроек из конфигурационного файла
    def loadConfig(self, filename):
        Config = ConfigParser.ConfigParser()
        Config.read(filename)

        s = ''
        
        try:
            self.SetLong(res.EDIT_START_COLOR, self.getColorId(Config.get(res.STR_CFG_SECTION, res.STR_CFG_START_COLOR)))
        except Exception as e:
            s += self.loadConfigError(res.STR_CFG_START_COLOR, type(e).__name__)
        self.SetString(res.EDIT_POINTS_FREQ, Config.get(res.STR_CFG_SECTION, res.STR_CFG_POINTS_FREQ))
        self.SetString(res.EDIT_COLORS_FREQ, Config.get(res.STR_CFG_SECTION, res.STR_CFG_COLORS_FREQ))
        self.SetString(res.EDIT_SCALE_X, Config.get(res.STR_CFG_SECTION, res.STR_CFG_SCALE_X))
        self.SetString(res.EDIT_SCALE_Y, Config.get(res.STR_CFG_SECTION, res.STR_CFG_SCALE_Y))
        self.SetString(res.EDIT_SCALE_Z, Config.get(res.STR_CFG_SECTION, res.STR_CFG_SCALE_Z))
        self.SetString(res.EDIT_LAT, Config.get(res.STR_CFG_SECTION, res.STR_CFG_LAT))
        self.SetString(res.EDIT_LON, Config.get(res.STR_CFG_SECTION, res.STR_CFG_LON))
        self.SetString(res.EDIT_PREFIX, Config.get(res.STR_CFG_SECTION, res.STR_CFG_PREFIX))
        self.SetString(res.EDIT_OUTPUT_FOLDER, Config.get(res.STR_CFG_SECTION, res.STR_CFG_OUTPUT_FOLDER))
        self.SetString(res.EDIT_TEMPLATE_PATH, Config.get(res.STR_CFG_SECTION, res.STR_CFG_TEMPLATE_PATH))
        self.SetString(res.EDIT_MAX_VELOCITY, Config.get(res.STR_CFG_SECTION, res.STR_CFG_MAX_VELOCITY))
        self.SetString(res.EDIT_MIN_DISTANCE, Config.get(res.STR_CFG_SECTION, res.STR_CFG_MIN_DISTANCE))
        self.SetString(res.EDIT_HEIGHT_OFFSET, Config.get(res.STR_CFG_SECTION, res.STR_CFG_HEIGHT_OFFSET))
        self.SetString(res.EDIT_ROTATION, Config.get(res.STR_CFG_SECTION, res.STR_CFG_ROTATION))
        self.SetString(res.EDIT_OBJECT_COUNT, Config.get(res.STR_CFG_SECTION, res.STR_CFG_OBJECT_COUNT))

        if s is not '':
            s = 'In {}:\n'.format(filename) + s
            RaiseErrorMessage(s)

    # по сути, загрузка конфигурации по-умолчанию заполняет интерфейс необходимыми значениями     
    def loadConfigDefault(self):
        if self.plugin.default_config_path is not None:
            self.loadConfig(self.plugin.default_config_path)      
            self.SetString(res.EDIT_TIME_START, 0)
            self.SetString(res.EDIT_TIME_END, 0)      
        else:
            RaiseErrorMessage('Default config file not found')
        
    def loadConfigAskFilename(self):
        filename = c4d.storage.LoadDialog(title="Choose template file", flags=c4d.FILESELECT_LOAD, def_path=self.plugin.module_path, def_file="default.ini")
        if filename is not None:
            self.loadConfig(filename)

    def addHeaderSection(self):
        self.GroupBegin(0, c4d.BFH_LEFT | c4d.BFH_SCALEFIT, cols=4, rows=1)
        self.AddStaticText(res.TEXT_DOCINFO, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)        
        self.AddStaticText(res.TEXT_CFG_FILE, c4d.BFH_RIGHT, name="Config:")
        self.AddButton(res.BUTTON_LOAD_CONFIG, c4d.BFH_RIGHT, name="Load...")
        self.AddButton(res.BUTTON_SAVE_CONFIG, c4d.BFH_RIGHT, name="Save...")
        self.GroupEnd()

    def addStartColorSection(self):
        self.AddStaticText(res.TEXT_START_COLOR, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Start color:")
        self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=2, rows=1)
        self.AddRadioGroup(res.EDIT_START_COLOR, c4d.BFH_SCALEFIT | c4d.BFV_TOP, columns=5, rows=1)
        self.AddChild(res.EDIT_START_COLOR, res.COLOR_RED, "Red")
        self.AddChild(res.EDIT_START_COLOR, res.COLOR_ORANGE, "Orange")
        self.AddChild(res.EDIT_START_COLOR, res.COLOR_YELLOW, "Yellow")
        self.AddChild(res.EDIT_START_COLOR, res.COLOR_CYAN, "Cyan")
        self.AddChild(res.EDIT_START_COLOR, res.COLOR_PURPLE, "Purple")
        self.GroupEnd()

    def addAnimationIdSection(self):
        self.AddStaticText(res.TEXT_ANIMATION_ID, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Animation ID:")
        self.AddEditText(res.EDIT_ANIMATION_ID, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)

    def addPointsFreqSection(self):
        self.AddStaticText(res.TEXT_POINTS_FREQ, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Points frequency for capture animation (Hz):")
        self.AddEditText(res.EDIT_POINTS_FREQ, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)

    def addColorsFreqSection(self):
        self.AddStaticText(res.TEXT_COLORS_FREQ, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Colors frequency for capture animation (Hz):")
        self.AddEditText(res.EDIT_COLORS_FREQ, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)

    def addPartialScaleSection(self):
        self.AddStaticText(res.TEXT_SCALE_PARTIAL, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Partial scale factor (x, y, z):")
        self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=3, rows=1)
        self.AddEditText(res.EDIT_SCALE_X, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        self.AddEditText(res.EDIT_SCALE_Y, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        self.AddEditText(res.EDIT_SCALE_Z, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        self.GroupEnd()

    def addOriginSection(self):
        self.AddStaticText(res.TEXT_LAT_LON_PARTIAL, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Local origin (lat, lon; degrees):")
        self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=3, rows=1)
        self.AddEditText(res.EDIT_LAT, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        self.AddEditText(res.EDIT_LON, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        self.GroupEnd()

    def addRotateSection(self):
        self.AddStaticText(res.TEXT_ROTATION, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Horizontal rotation (counter clockwise; degrees):")
        self.AddEditText(res.EDIT_ROTATION, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        
    def addOffsetSection(self):
        self.AddStaticText(res.TEXT_HEIGHT_OFFSET, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Height offset (m):")
        self.AddEditText(res.EDIT_HEIGHT_OFFSET, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)

    def addPrefixSection(self):
        self.AddStaticText(res.TEXT_PREFIX, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Object's name prefix:")
        self.AddEditText(res.EDIT_PREFIX, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        
    def addObjCountSection(self):
        self.AddStaticText(res.TEXT_OBJECT_COUNT, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Object count:")
        self.AddEditText(res.EDIT_OBJECT_COUNT, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)

    def addMaxVelocitySection(self):
        self.AddStaticText(res.TEXT_MAX_VELOCITY, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Max velocity check (0 for uncheck; m/s):")
        self.AddEditText(res.EDIT_MAX_VELOCITY, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)

    def addMinDistanceSection(self):
        self.AddStaticText(res.TEXT_MIN_DISTANCE, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Min distance check (0 for uncheck; m):")
        self.AddEditText(res.EDIT_MIN_DISTANCE, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        
    def addTemplateSection(self):
        self.AddStaticText(res.TEXT_TEMPLATE_PATH, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="LUA script template:")
        self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=2, rows=1)
        edit_template_path = self.AddEditText(res.EDIT_TEMPLATE_PATH, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        # self.Enable(edit_template_path, False)
        self.AddButton(res.BUTTON_TEMPLATE_PATH, c4d.BFH_RIGHT, name="Open...")
        self.GroupEnd()        
        
    def addOutputFolderSection(self):
        self.AddStaticText(res.TEXT_OUTPUT_FOLDER, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Output folder for generated scripts:")
        self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=2, rows=1)
        edit_output_folder = self.AddEditText(res.EDIT_OUTPUT_FOLDER, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        # self.Enable(edit_output_folder, False)
        self.AddButton(res.BUTTON_OUTPUT_FOLDER, c4d.BFH_RIGHT, name="Open...")
        self.GroupEnd()

    def addTimeSection(self):
        self.AddStaticText(res.TEXT_TIME, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Time (start, end; set equal to disable; sec):")
        self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=2, rows=1)
        self.AddEditText(res.EDIT_TIME_START, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        self.AddEditText(res.EDIT_TIME_END, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        self.GroupEnd()

    def CreateLayout(self):
        self.SetTitle('Geoscan Drone Air Show')
        
        # Layout flag that will cause the widget to be scaled as much
        # possible in horizontal and vertical direction.
        BF_FULLFIT = c4d.BFH_CENTER | c4d.BFV_SCALEFIT
        
        # Создание главной группы, включающей в себя весь интерфейс
        self.GroupBegin(0, BF_FULLFIT, cols=1, rows=0)
        self.GroupBorderSpace(4, 4, 4, 4)

        self.addHeaderSection()

        self.LayoutFlushGroup(c4d.ID_SCROLLGROUP_STATUSBAR_EXTLEFT_GROUP)

        # Создаем группу-таблицу | текст | поле редактиирования |
        self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=2, rows=6)
        self.param_initw = 450

        self.addStartColorSection()
        self.addPointsFreqSection()
        self.addColorsFreqSection()
        self.addPartialScaleSection()
        self.addOriginSection()
        self.addRotateSection()
        self.addOffsetSection()
        self.addPrefixSection()
        self.addObjCountSection()
        self.addMinDistanceSection()
        self.addMaxVelocitySection()
        self.addTemplateSection()
        self.addOutputFolderSection()
        self.addTimeSection()

        self.GroupEnd()

        self.AddButton(res.BUTTON_GENERATE, c4d.BFH_CENTER, initw=130, name="Generate")

        self.loadConfigDefault()
        self.Refresh()
        self.GroupEnd()
        self.LayoutChanged(c4d.ID_SCROLLGROUP_STATUSBAR_EXTLEFT_GROUP)
        return True
        
    def Command(self, param, bc):
        if param == res.BUTTON_OUTPUT_FOLDER:
            filename = c4d.storage.LoadDialog(title="Choose folder to store files", flags=c4d.FILESELECT_DIRECTORY)
            if not filename is None:
                self.output_folder = filename
                self.SetString(res.EDIT_OUTPUT_FOLDER, filename)
                return True
            else:
                return False

        if param == res.BUTTON_TEMPLATE_PATH:
            filename = c4d.storage.LoadDialog(title="Choose template file", flags=c4d.FILESELECT_LOAD, def_path=self.plugin.module_path, def_file="c4d_animation.lua")
            if not filename is None:
                self.template_path = filename
                self.SetFilename(res.EDIT_TEMPLATE_PATH, self.template_path)
                return True
            else:
                return False

        if param == res.BUTTON_LOAD_CONFIG:
            self.loadConfigAskFilename()

        if param == res.BUTTON_SAVE_CONFIG:
            self.saveConfig()

        elif param == res.BUTTON_GENERATE:
            error_string = ''
            points_freq = colors_freq = scale_x = scale_y = scale_z = lat = lon = max_velocity = height_offset = time_start = time_end = None
            try:
                points_freq = float(self.GetString(res.EDIT_POINTS_FREQ))
                colors_freq = float(self.GetString(res.EDIT_COLORS_FREQ))
                scale_x = float(self.GetString(res.EDIT_SCALE_X))
                scale_y = float(self.GetString(res.EDIT_SCALE_Y))
                scale_z = float(self.GetString(res.EDIT_SCALE_Z))
                lat = float(self.GetString(res.EDIT_LAT))
                lon = float(self.GetString(res.EDIT_LON))
                rotation =  float(self.GetString(res.EDIT_ROTATION))
                height_offset = float(self.GetString(res.EDIT_HEIGHT_OFFSET))
                max_velocity = float(self.GetString(res.EDIT_MAX_VELOCITY))
                min_distance = float(self.GetString(res.EDIT_MIN_DISTANCE))
                time_start = float(self.GetString(res.EDIT_TIME_START))
                time_end = float(self.GetString(res.EDIT_TIME_END))
            except:
                error_string += 'Invalid floating point number\n'
                pass
            start_color = self.getColorName(self.GetLong(res.EDIT_START_COLOR))
            # animation_id = int(self.GetString(res.EDIT_ANIMATION_ID))
            prefix = self.GetString(res.EDIT_PREFIX)
            object_count =  int(self.GetString(res.EDIT_OBJECT_COUNT))
            template_path = self.GetString(res.EDIT_TEMPLATE_PATH)
            output_folder = self.GetString(res.EDIT_OUTPUT_FOLDER)

            if start_color is None or points_freq is None or colors_freq is None or scale_x is None or scale_y is None or scale_z is None or prefix is None or object_count is None or max_velocity is None or output_folder is None:
                error_string += 'Not all values specified.\n'
            # проверяем адекватность введённых значений
            if points_freq <= 0 or colors_freq <= 0:
                error_string += 'Frequency cannot be less than 0 fps.\n'
            if points_freq > 20:
                error_string += 'Points frequency cannot be more than 20 fps.\n'
            if colors_freq > 60:
                error_string += 'Colors frequency cannot be more than 60 fps.\n'
            if points_freq > colors_freq:
                error_string += 'Points frequency cannot be more than colors frequency.\n'
            if colors_freq % points_freq:
                error_string += 'Points and colors frequencies must be proportional.\n'
            if rotation < 0 or rotation > 360:
                error_string += 'Rotation must be in range 0-360 degrees\n'
            if object_count < 1:
                error_string += 'Object count must be a natural number more than 1'
            if (not os.path.exists(template_path)):
                error_string += 'No *.lua script template specified.\n'
            if (not os.path.exists(output_folder)):
                error_string += 'Not valid output folder specified.\n'
            if time_start > time_end:
                error_string += 'Time start cannot be more than time end'
            if time_start < 0 or time_end < 0:
                error_string += 'Time cannot be less than 0 sec'
            max_time = self.current_doc.GetMaxTime().Get()
            if time_end > max_time:
                error_string += 'End time cannot be more than document max time ({} sec)'.format(round(max_time, 2))

            if len(error_string) > 0:
                RaiseErrorMessage(error_string)
                return False
            else:
                print(("\n\n{:-^60}\n\n"
                    "File: {}\n"
                    "Params:\nStart color = {}, Points frequency = {} Hz, Colors frequency = {} Hz\n"
                    "Scale: x = {}, y = {}, z = {}, Rotation = {} deg\n"
                    "Height offset = {} m, Prefix = {}, Object count = {}, Min distance = {}, Max velocity = {}\n"
                    "Template: {}\nOutput folder: {}\n").format('STARTING GENERATION', self.current_doc.GetDocumentName(),
                    start_color, points_freq, colors_freq, scale_x, scale_y, scale_z, rotation, height_offset,
                    prefix, object_count, min_distance, max_velocity, template_path, output_folder))
                # прокидываем значения в модуль для выполнения
                self.plugin.initVars()
                animation_id_color = int(self.getColorHue(start_color)*255/360) # convert hue to int format
                self.plugin.animation_id = animation_id_color
                self.plugin.points_freq = points_freq
                self.plugin.colors_freq = colors_freq
                self.plugin.scale_x = scale_x
                self.plugin.scale_y = scale_y
                self.plugin.scale_z = scale_z
                self.plugin.lat = lat
                self.plugin.lon = lon
                self.plugin.height_offset = height_offset * 100
                self.plugin.prefix = prefix
                self.plugin.rotation = rotation
                self.plugin.object_count = object_count
                self.plugin.max_velocity = max_velocity
                self.plugin.min_distance = min_distance
                self.plugin.template_path = template_path
                self.plugin.output_folder = output_folder
                if time_start == time_end:
                    self.plugin.time_start = None
                    self.plugin.time_end = None
                else:
                    self.plugin.time_start = time_start
                    self.plugin.time_end = time_end
                self.plugin.main()
                return True

        return False
        
    def CoreMessage(self, kind, bc):
        r""" Responds to what's happening inside of Cinema 4D. In this
        case, we're looking to see if the active document has changed. """

        # One case this message is being sent is when the active
        # document has changed.
        if kind == c4d.EVMSG_DOCUMENTRECALCULATED:
            self.Refresh()

        return True

# данный класс регистрирует плагин и создаёт команду конвертации движения объектов в LUA-скрипт для квадрокоптеров
class c4d_capture(c4d.plugins.CommandData):
    r""" The purpose of this plugin is to convert
    Cinema 4D scenes into Geoscan "Pioneer" drone code. """
    
    STRUCT_FORMAT = "IhhHBBB"
    POINTS_FOLDER_NAME = "./points/"
    LUA_FOLDER_NAME = "./scripts/"
    BIN_FOLDER_NAME = "./bins/"
    
    def __init__(self):
        self.module_path = os.path.dirname(__file__) # папка, в которой хранится модуль, очень полезна
        self.default_config_path = self.module_path + "\default.ini"
        self.template_path = self.module_path + "/c4d_animation.lua" #путь до шаблона также обязателен
    
    def initVars(self):
        self.animation_id = None
        self.points_freq = None
        self.colors_freq = None
        self.time_step = None
        self.object_count = None
        self.max_velocity = None
        self.min_distance = None
        self.scale_x = None
        self.scale_y = None
        self.scale_z = None
        self.lat = None
        self.lon = None
        self.rotation = None
        self.height_offset = None
        self.prefix = None
        self.output_folder = None
        self.time_start = None
        self.time_end = None
        self.notakeoff = []
        self.module_path = None
        self.template_path = None

    def Register(self):
        help_string = 'Geoscan capture plugin: convert Cinema 4D' \
                      'scene into drone code.'
                      
        # подгружаем иконку для плагина, если это возможно
        ico = c4d.bitmaps.BaseBitmap()
        if ico.InitWith(self.module_path + "\\geoscan.ico")[0] != c4d.IMAGERESULT_OK:
            ico = None # если не вышло подгрузить, иконку не передаём

        return c4d.plugins.RegisterCommandPlugin(
                PLUGIN_ID,                   # The Plugin ID, obviously
                "Geoscan Drone Air Show",  # The name of the plugin
                c4d.PLUGINFLAG_COMMAND_HOTKEY,    # Sort of options
                ico,                        # Icon, Geoscan here
                help_string,                 # The help text for the command
                self,                        # The plugin implementation
        )

    def getPointsFolder(self):
        return os.path.dirname(self.output_folder + self.POINTS_FOLDER_NAME) + "/"
        
    def getLuaFolder(self):
        return os.path.dirname(self.output_folder + self.LUA_FOLDER_NAME) + "/"

    def getBinsFolder(self):
        return os.path.dirname(self.output_folder + self.BIN_FOLDER_NAME) + "/"

    def getNames(self):
        names = []
        # activeObjectName = self.getActiveObjectName()
        for indexName in range(self.object_count):
            name = self.prefix + "{0:d}".format(indexName) # Count from 1 in animation objects
            names.append(name)
            
        return names

    def getObjects(self, objectNames):
        objects = []
        for objectName in objectNames:
            obj = self.doc.SearchObject(objectName)
            if obj == None:
                #print ("Object {0:s} doesn't exist".format(objectName))
                raise GenerationError(console='Object with name \"{0:s}\" doesn\'t exist'.format(objectName),
                    dialog='Not all objects with specified names exist')
            else:
                objects.append(obj)
        return objects

    def getPositions(self, objects):
        vecPosition = []
        for obj in objects:
            vec = self.getPosition(obj)
            # vec.y += self.height_offset
            vecPosition.append(vec)
        return vecPosition
        
    def getDocInfo(self):
        self.doc = documents.GetActiveDocument()
        self.fps = self.doc.GetFps()
        self.max_time = self.doc.GetMaxTime().Get()
        self.time_step = 1/self.colors_freq
        self.max_time = (self.max_time // self.time_step + 2) * self.time_step
        self.max_points = int((self.max_time - self.time_step) / self.time_step)

        self.objNames = self.getNames()
        self.objects = self.getObjects(self.objNames)

    def getTimeRange(self):
        if self.time_start is not None and self.time_end is not None:
            time_start = self.time_start
            time_end = self.time_end
        else:
            time_start = 0
            time_end = self.max_time
        return time_start, time_end

    def checkTimeRange(self, start, end):
        if (end - start) > 600:
            continue_generation = gui.QuestionDialog('Animation duration is {}, it\'s more than 10 minutes.\nContinue generation?'.format(end-start))
            if not continue_generation:
                raise GenerationError(console='Animation duration is more than 600 seconds ' \
                    '(start: {} sec, end: {} sec)'.format(start,end))

    def updateView(self, time):
        self.shot_time = c4d.BaseTime(time)
        self.doc.SetTime(self.shot_time)
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_REDUCTION | c4d.DRAWFLAGS_NO_THREAD)

    def initArrays(self):
        self.positionsArray = self.getPositions(self.objects)
        self.positionsArrayPrev = self.positionsArray
        self.points_array = []
        self.collisions_array = []
        self.velocities_array = []
        self.excess_velocity_array = [self.max_velocity] * self.object_count
        self.excess_start_array = [0] * self.object_count
        self.excess_frames_array = [0] * self.object_count
        self.collision_distance_array = [ [self.min_distance] * self.object_count for _ in range(self.object_count)]
        self.collision_start_array = [ [0] * self.object_count for _ in range(self.object_count)]

        for i in range(self.object_count):
            s = '-- Time step is {0:.2f} s\n'\
                '-- Maximum number of points is {1}\n'\
                '-- [time]=cs, [x][y][z]=cm, [r][g][b]=0-255\n'\
                'local points  =  "'.format(self.time_step, self.max_points)
            self.points_array.append([s])

    def checkZeroAlt(self):
        initNonZeroAltObjects = []
        for i in range(self.object_count):
            if int(self.positionsArray[i].y) > 0:
                initNonZeroAltObjects.append(i)
        if initNonZeroAltObjects != []:
            console = 'Copters with non zero altitude on start: ' + str(initNonZeroAltObjects).strip('[]')
            raise GenerationError(console=console, dialog='Not all copters have zero altitude on start.')

    def getColor(self, obj):
        try:
            objMaterial = obj.GetTag(Ttexture).GetMaterial()
        except AttributeError:
            # print ("First object tag must be Material")
            RaiseErrorMessage("Didn't find object's ({0:s}) tag \"Material\"".format(self.obj.GetName()))
            return
        vecRGB = objMaterial.GetAverageColor(c4d.CHANNEL_COLOR) # получаем RGB

        return vecRGB

    def getPosition(self, obj):
        #Get position
        vecPosition = obj.GetAbsPos()

        objScale = obj.GetAbsScale()

        # масштабирование пространственного вектора
        vecPosition.x = vecPosition.x * self.scale_x / abs(objScale.x)
        vecPosition.y = vecPosition.y * self.scale_y / abs(objScale.y)
        vecPosition.z = vecPosition.z * self.scale_z / abs(objScale.z)
        
        #поворот в пространстве вдоль оси OY (направлена вверх)
        if self.rotation == 0 or self.rotation == 360:
            rot_rad = self.rotation*math.pi/180
            vecPosition.x = math.cos(rot_rad)*vecPosition.x - math.sin(rot_rad)*vecPosition.z
            vecPosition.z = math.sin(rot_rad)*vecPosition.x + math.cos(rot_rad)*vecPosition.z

        # подъём сцены на некоторую высоту
        # vecPosition.y = vecPosition.y + self.height_offset

        return vecPosition

    def getData(self, time, objNumber, vecPosition, vecRGB):
        data = []
        try:
            s = struct.pack(self.STRUCT_FORMAT,
                                        int(time * 100),   #I
                                        int(vecPosition.x), #h
                                        int(vecPosition.z), #h
                                        int(vecPosition.y), #H
                                        int(vecRGB.x * 255), #B
                                        int(vecRGB.y * 255), #B
                                        int(vecRGB.z * 255)) #B
        except struct.error:
            console = 'Data out of format range for object \'{}\':\nTime = {} / should be int\nx = {}, y = {}, z = {} / should be short\nred = {}, green = {}, blue = {} / should be unsigned char'.format(
                                        (self.prefix + str(objNumber)),
                                        (time * 100),
                                        (vecPosition.x),
                                        (vecPosition.z),
                                        (vecPosition.y),
                                        (vecRGB.x * 255),
                                        (vecRGB.y * 255),
                                        (vecRGB.z * 255))
            raise GenerationError(console=console, dialog='Data out of format range.')
        if int(vecPosition.y) > 0:# (self.height_offset): # append if altitude greater than 0 in animation
            s_xhex = binascii.hexlify(s)
            self.points_array[objNumber].append(''.join([r'\x' + s_xhex[i:i+2] for i in range(0, len(s_xhex), 2)]))
            data = [time,
                    vecPosition.x,
                    vecPosition.z,
                    vecPosition.y,
                    int(vecRGB.x * 255),
                    int(vecRGB.y * 255),
                    int(vecRGB.z * 255)]
        return data

    def checkVelocity(self, time, time_end):
        for i in range(1, self.object_count):
            if int(self.positionsArray[i].y) > 0:#(self.height_offset):
                distance = pow(((self.positionsArray[i].x - self.positionsArrayPrev[i].x) ** 2 + (self.positionsArray[i].y - self.positionsArrayPrev[i].y) ** 2 + (self.positionsArray[i].z - self.positionsArrayPrev[i].z) ** 2), 0.5) / 100 # /100 - convert cm to m
                velocity = distance / self.time_step
                if velocity > self.max_velocity:
                    self.excess_frames_array[i] = 0
                    if self.excess_start_array[i] == 0:
                        self.excess_start_array[i] = time
                    if velocity > self.excess_velocity_array[i]:
                        self.excess_velocity_array[i] = velocity
                elif self.excess_start_array[i] != 0:
                    if self.excess_frames_array[i] > int(self.colors_freq):
                        start_time = self.excess_start_array[i]
                        end_time = time - self.excess_frames_array[i]*self.time_step
                        s = "Velocity of\t{:03d}\tis up to\t{:.2f} m/s\tTime: {:.2f}-{:.2f} s\tFrames: {}-{}".format(i, self.excess_velocity_array[i], start_time, end_time, int(start_time*self.fps), int(end_time*self.fps))
                        self.velocities_array.append(s)
                        self.excess_start_array[i] = 0
                        self.excess_frames_array[i] = 0
                    else:
                        self.excess_frames_array[i] += 1
            if self.excess_start_array[i] != 0 and (time + self.time_step) > time_end:
                start_time = self.excess_start_array[i]
                end_time = time - self.excess_frames_array[i]*self.time_step
                s = "Velocity of\t{:03d}\tis up to\t{:.2f} m/s\tTime: {:.2f}-{:.2f} s\tFrames: {}-{}".format(i, self.excess_velocity_array[i], start_time, end_time, int(start_time*self.fps), int(end_time*self.fps))
                self.velocities_array.append(s)
                self.excess_start_array[i] = 0
                self.excess_frames_array[i] = 0

    def checkDistance(self, time, time_end):
        for j in range(self.object_count-1):
            for k in range(j+1, self.object_count):
                x1 = self.positionsArray[j].x
                y1 = self.positionsArray[j].y
                z1 = self.positionsArray[j].z
                x2 = self.positionsArray[k].x
                y2 = self.positionsArray[k].y
                z2 = self.positionsArray[k].z
                if int(y1) > 0 and int(y2) > 0: #(self.height_offset) and int(y2) > (self.height_offset):
                    distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2) / 100 # /100 - convert cm to m
                    if distance < self.min_distance:
                        if self.collision_start_array[j][k] == 0:
                            self.collision_start_array[j][k] = time
                        if distance < self.collision_distance_array[j][k]:
                            self.collision_distance_array[j][k] = distance
                    elif self.collision_start_array[j][k] != 0:
                            start_time = self.collision_start_array[j][k]
                            end_time = time - self.time_step
                            s = "Collision between:\t{:03d}\tand\t{:03d}\tMin distance: {:.2f} m\tTime: {:.2f}-{:.2f} s\tFrames: {}-{}".format(j, k, self.collision_distance_array[j][k], start_time, end_time, int(start_time*self.fps), int(end_time*self.fps))
                            self.collisions_array.append(s)
                            self.collision_start_array[j][k] = 0
                            self.collision_distance_array[j][k] = self.min_distance
                if self.collision_start_array[j][k] != 0 and (time + self.time_step) > time_end:
                    start_time = self.collision_start_array[j][k]
                    end_time = time - self.time_step
                    s = "Collision between:\t{:03d}\tand\t{:03d}\tMin distance: {:.2f} m\tTime: {:.2f}-{:.2f} s\tFrames: {}-{}".format(j, k, self.collision_distance_array[j][k], start_time, end_time, int(start_time*self.fps), int(end_time*self.fps))
                    self.collisions_array.append(s)
                    self.collision_start_array[j][k] = 0
                    self.collision_distance_array[j][k] = self.min_distance
    
    def printConsoleOutput(self):
        msg_collision = "\nTOTAL NUMBER OF COLLISIONS: {}".format(len(self.collisions_array))
        msg_velocities = "\nTOTAL NUMBER OF VELOCITY EXCESS: {}".format(len(self.velocities_array))
        print "\n"
        if self.notakeoff:
            print('Drones ' + str(self.notakeoff).strip('[]') + ' have no takeoff. This files are not generated.\n')
        if len(self.collisions_array) > 0:
            for s in self.collisions_array:
                print s
            print "\n"
            RaiseErrorMessage(msg_collision)
        if len(self.velocities_array) > 0:
            for s in self.velocities_array:
                print s
            print "\n"
            RaiseErrorMessage(msg_velocities)
        print msg_collision
        print msg_velocities

    def writeScriptFile(self):
        if not os.path.exists(os.path.dirname(self.getPointsFolder())):
            try:
                os.makedirs(os.path.dirname(self.getPointsFolder()))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        for i in range(self.object_count):
            fileName = self.getPointsFolder() + self.objNames[i] + ".lua"
            with open(fileName, "w") as f:
                for item in self.points_array[i]:
                    f.write(item)
                s = "local points_count = {0:d}\n" \
                    "local str_format = \"{1:s}\"\n" \
                    "local origin_lat = {2:f}\n" \
                    "local origin_lon = {3:f}\n" \
                    "--print (\"t, s:\tx, m:\ty, m:\tz, m:\tr, byte:\tg, byte:\tb, byte:\")\n" \
                    "--for n = 0, {0:d} do\n" \
                    "    --t, x, y, z, r, g, b, _ = string.unpack(str_format, points, 1 + n * string.packsize(str_format))\n" \
                    "    --print (string.format(\"%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t\t%.2f\t\t%.2f\t\t\", t/100, x/100, y/100, z/100, r/255, g/255, b/255))\n" \
                    "--end\n".format(len(self.points_array[i])-2, self.STRUCT_FORMAT, self.lat, self.lon)
                f.write(s)

        if not os.path.exists(os.path.dirname(self.getLuaFolder())):
            try:
                os.makedirs(os.path.dirname(self.getLuaFolder()))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        for i in range(self.object_count):
            pointsFileName = self.getPointsFolder() + self.objNames[i] + ".lua"
            with open(pointsFileName, "r") as f_points, open(self.template_path, "r") as f_temp, open(self.getLuaFolder() + self.objNames[i] + ".lua", "w") as f:
                f.write(f_points.read())
                #f.write("\n")
                f.write(f_temp.read())

    def writeBinFile(self, data):
        if not os.path.exists(os.path.dirname(self.getBinsFolder())):
            try:
                os.makedirs(os.path.dirname(self.getBinsFolder()))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        for i in range(self.object_count):
            if data[i] == []:
                self.notakeoff.append(i)
                continue
            points_count = len(self.points_array[i])-2
            freq_ratio = self.colors_freq/self.points_freq
            fileName = self.getBinsFolder() + self.objNames[i] + ".bin"
            with open(fileName, "wb") as f:
                f.write(b'\xaa\xbb\xcc\xdd')

                Version = 1
                AnimationId = self.animation_id
                PointsFreq = self.points_freq
                ColorsFreq = self.colors_freq
                PointsFormat = 4
                ColorsFormat = 1
                PointsNumber = points_count//freq_ratio
                ColorsNumber = points_count
                TimeStart = data[i][0][0]
                TimeEnd = data[i][-1][0]
                OriginLat = self.lat
                OriginLon = self.lon
                AltOrigin = 0.0
                HeaderFormat = '<BBBBBBHHfffff'
                size = struct.calcsize(HeaderFormat)

                f.write(struct.pack(HeaderFormat,   Version,
                                                    AnimationId,
                                                    PointsFreq,
                                                    ColorsFreq,
                                                    PointsFormat,
                                                    ColorsFormat,
                                                    PointsNumber,
                                                    ColorsNumber,
                                                    TimeStart,
                                                    TimeEnd,
                                                    OriginLat,
                                                    OriginLon,
                                                    AltOrigin))

                for _ in range(size + 4, 100):
                    f.write(b'\x00')

                counter = 0
                for k in range(0, points_count, int(freq_ratio)):
                    data[i][k][3] += self.height_offset
                    f.write(struct.pack('<fff', *[pos/100 for pos in data[i][k][1:4]]))
                    counter += 1

                if counter < 1800:
                    for _ in range(counter, 1800):
                        f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

                for k in range(points_count):
                    f.write(struct.pack('<BBB', *data[i][k][4:7]))

    def finish(self):
        if self.notakeoff:
            RaiseErrorMessage("Not all files are generated. Some copters have no takeoff.\n\nPlease, check results in console output.\nMain menu->Script->Console")
        else:
            RaiseMessage("Files are generated.\n\nPlease, check collisions in console output.\nMain menu->Script->Console")

    def main(self):
        try:
            self.getDocInfo()
            time_start, time_end = self.getTimeRange()
            self.checkTimeRange(time_start, time_end)
            self.updateView(time_start)
            self.initArrays()
            self.checkZeroAlt()

            dataArray = [[] for _ in range(self.object_count)]
            time = time_start
            while time <= time_end:
                self.updateView(time)
                self.positionsArrayPrev = [_ for _ in self.positionsArray]
                objNumber = 0
                for obj in self.objects:
                    position = self.getPosition(obj)
                    self.positionsArray[objNumber] = position
                    if int(position.y) > 0:
                        color = self.getColor(obj)
                        data = self.getData(time, objNumber, position, color)
                        dataArray[objNumber].append(data)
                    objNumber += 1
                if self.min_distance > 0:
                    self.checkDistance(time, time_end)
                if self.max_velocity > 0:
                    self.checkVelocity(time, time_end)
                time += self.time_step

            self.writeBinFile(dataArray)
            self.writeScriptFile()
            self.printConsoleOutput()

            self.finish()
        except GenerationError:
            return
                
    @property
    def dialog(self):
        if not hasattr(self, '_dialog'): # диалог единственный на весь модуль
            self._dialog = PioneerCaptureDialog()
            self._dialog.plugin = self
        return self._dialog

    def Execute(self, doc):
        return self.dialog.Open(c4d.DLG_TYPE_ASYNC, PLUGIN_ID)

    def RestoreLayout(self, secret):
        return self.dialog.Restore(PLUGIN_ID, secret)


if __name__=="__main__":
    c4d_capture().Register()