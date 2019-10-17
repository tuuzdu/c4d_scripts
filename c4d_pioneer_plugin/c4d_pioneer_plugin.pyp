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
class PioneerCaptureDialog(c4d.gui.GeDialog):

    def __init__(self):
        self.current_doc = c4d.documents.GetActiveDocument()
        self.output_folder = None # по умолчанию папка вывода скриптов не выбрана (можно исправить на пользовательские опции)

    def Refresh(self, flush=True, force=False, initial=False, reload_=False):
        current_doc = c4d.documents.GetActiveDocument()
        title_text = "Project: %s" % current_doc.GetDocumentName()
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
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_OBJECT_COUNT, self.GetInt32(res.EDIT_OBJECT_COUNT))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_MAX_VELOCITY, self.GetString(res.EDIT_MAX_VELOCITY))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_MIN_DISTANCE, self.GetString(res.EDIT_MIN_DISTANCE))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_ROTATION, self.GetInt32(res.EDIT_ROTATION))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_TEMPLATE_PATH, self.GetString(res.EDIT_TEMPLATE_PATH))
        Config.set(res.STR_CFG_SECTION, res.STR_CFG_OUTPUT_FOLDER, self.GetString(res.EDIT_OUTPUT_FOLDER))
        Config.write(cfgfile)
        cfgfile.close()
     
    # по сути, загрузка конфигурации по-умолчанию заполняет интерфейс необходимыми значениями     
    def loadConfigDefault(self):
        self.loadConfig(self.plugin.module_path + "\default.ini")
        
    def loadConfigAskFilename(self):
        filename = c4d.storage.LoadDialog(title="Choose template file", flags=c4d.FILESELECT_LOAD, def_path=self.plugin.module_path, def_file="default.ini")
        if filename is None:
            return
        self.loadConfig(filename)

    # функция для загрузки настроек из конфигурационного файла
    def loadConfig(self, filename):

        Config = ConfigParser.ConfigParser()
        Config.read(filename)

        self.SetLong(res.EDIT_START_COLOR, self.getColorId(Config.get(res.STR_CFG_SECTION, res.STR_CFG_START_COLOR)))
        # self.SetInt32(res.EDIT_ANIMATION_ID, Config.getint(res.STR_CFG_SECTION, res.STR_CFG_ANIMATION_ID))
        self.SetString(res.EDIT_POINTS_FREQ, Config.getfloat(res.STR_CFG_SECTION, res.STR_CFG_POINTS_FREQ))
        self.SetString(res.EDIT_COLORS_FREQ, Config.getfloat(res.STR_CFG_SECTION, res.STR_CFG_COLORS_FREQ))
        self.SetString(res.EDIT_SCALE_X, Config.getfloat(res.STR_CFG_SECTION, res.STR_CFG_SCALE_X))
        self.SetString(res.EDIT_SCALE_Y, Config.getfloat(res.STR_CFG_SECTION, res.STR_CFG_SCALE_Y))
        self.SetString(res.EDIT_SCALE_Z, Config.getfloat(res.STR_CFG_SECTION, res.STR_CFG_SCALE_Z))
        self.SetString(res.EDIT_LAT, Config.getfloat(res.STR_CFG_SECTION, res.STR_CFG_LAT))
        self.SetString(res.EDIT_LON, Config.getfloat(res.STR_CFG_SECTION, res.STR_CFG_LON))
        self.SetString(res.EDIT_PREFIX, Config.get(res.STR_CFG_SECTION, res.STR_CFG_PREFIX))
        self.SetString(res.EDIT_OUTPUT_FOLDER, Config.get(res.STR_CFG_SECTION, res.STR_CFG_OUTPUT_FOLDER))
        self.SetString(res.EDIT_TEMPLATE_PATH, Config.get(res.STR_CFG_SECTION, res.STR_CFG_TEMPLATE_PATH))
        self.SetString(res.EDIT_MAX_VELOCITY, Config.getfloat(res.STR_CFG_SECTION, res.STR_CFG_MAX_VELOCITY))
        self.SetString(res.EDIT_MIN_DISTANCE, Config.getfloat(res.STR_CFG_SECTION, res.STR_CFG_MIN_DISTANCE))
        self.SetString(res.EDIT_HEIGHT_OFFSET, Config.getfloat(res.STR_CFG_SECTION, res.STR_CFG_HEIGHT_OFFSET))
        self.SetInt32(res.EDIT_ROTATION, Config.getint(res.STR_CFG_SECTION, res.STR_CFG_ROTATION), min=0, max=360)
        self.SetInt32(res.EDIT_OBJECT_COUNT, Config.getint(res.STR_CFG_SECTION, res.STR_CFG_OBJECT_COUNT), min=1)

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
        # self.AddColorField(res.EDIT_START_COLOR, c4d.BFH_LEFT | c4d.BFH_SCALEFIT, initw=value_initw, colorflags=c4d.DR_COLORFIELD_ENABLE_HSV)
        # self.SetColorField(res.EDIT_START_COLOR, color = c4d.Vector(0,1,0), brightness = 1, maxbrightness = 1, flags=0)
        # print(int(c4d.utils.RGBToHSV(self.GetColorField(res.EDIT_START_COLOR)['color'])[0] * 1000))

    def addAnimationIdSection(self):
        self.AddStaticText(res.TEXT_ANIMATION_ID, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Animation ID:")
        self.AddEditNumber(res.EDIT_ANIMATION_ID, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)

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
        edit_scale_x = self.AddEditText(res.EDIT_SCALE_X, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        edit_scale_y = self.AddEditText(res.EDIT_SCALE_Y, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        edit_scale_z = self.AddEditText(res.EDIT_SCALE_Z, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        self.GroupEnd()

    def addOriginSection(self):
        self.AddStaticText(res.TEXT_LAT_LON_PARTIAL, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Local origin (lat, lon; degrees):")
        self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=3, rows=1)
        edit_lat = self.AddEditText(res.EDIT_LAT, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        edit_lon = self.AddEditText(res.EDIT_LON, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        self.GroupEnd()

    def addRotateSection(self):
        self.AddStaticText(res.TEXT_ROTATION, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Horizontal rotation (counter clockwise; degrees):")
        self.AddEditNumberArrows(res.EDIT_ROTATION, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        
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
        self.AddEditNumberArrows(res.EDIT_OBJECT_COUNT, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)

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
        self.Enable(edit_template_path, False)
        self.AddButton(res.BUTTON_TEMPLATE_PATH, c4d.BFH_RIGHT, name="Open...")
        # self.AddCheckBox(res.CHECKBOX_TEMPLATE_PATH, c4d.BFH_RIGHT, name="")
        self.GroupEnd()        
        
    def addOutputFolderSection(self):
        self.AddStaticText(res.TEXT_OUTPUT_FOLDER, c4d.BFH_RIGHT, initw=self.param_initw, borderstyle=c4d.BORDER_BLACK,
            name="Output folder for generated scripts:")
        self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=2, rows=1)
        edit_output_folder = self.AddEditText(res.EDIT_OUTPUT_FOLDER, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        self.Enable(edit_output_folder, False)
        self.AddButton(res.BUTTON_OUTPUT_FOLDER, c4d.BFH_RIGHT, name="Open...")
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
        self.param_initw = 450 # размер текстового поля

        self.addStartColorSection()
        # self.addAnimationIdSection()
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
        
        self.GroupEnd() # Конец группы-таблицы
        
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
                self.SetString(res.EDIT_TEMPLATE_PATH, self.template_path)
                return True
            else:
                return False
        if param == res.BUTTON_LOAD_CONFIG:
            self.loadConfigAskFilename()
        if param == res.BUTTON_SAVE_CONFIG:
            self.saveConfig()
        elif param == res.BUTTON_GENERATE:
            error_string = ''
            points_freq = colors_freq = scale_x = scale_y = scale_z = lat = lon = max_velocity = height_offset = None
            try:
                start_color = self.getColorName(self.GetLong(res.EDIT_START_COLOR))
                # animation_id = int(self.GetString(res.EDIT_ANIMATION_ID))
                points_freq = float(self.GetString(res.EDIT_POINTS_FREQ))
                colors_freq = float(self.GetString(res.EDIT_COLORS_FREQ))
                scale_x = float(self.GetString(res.EDIT_SCALE_X))
                scale_y = float(self.GetString(res.EDIT_SCALE_Y))
                scale_z = float(self.GetString(res.EDIT_SCALE_Z))
                lat = float(self.GetString(res.EDIT_LAT))
                lon = float(self.GetString(res.EDIT_LON))
                max_velocity = float(self.GetString(res.EDIT_MAX_VELOCITY))
                min_distance = float(self.GetString(res.EDIT_MIN_DISTANCE))
                height_offset = float(self.GetString(res.EDIT_HEIGHT_OFFSET))
            except:
                error_string = error_string + 'Invalid floating point number\n'
                pass
            prefix = self.GetString(res.EDIT_PREFIX)
            object_count =  self.GetInt32(res.EDIT_OBJECT_COUNT)
            rotation =  self.GetInt32(res.EDIT_ROTATION)
            template_path = self.GetString(res.EDIT_TEMPLATE_PATH)
            output_folder = self.GetString(res.EDIT_OUTPUT_FOLDER)

            if start_color is None or points_freq is None or colors_freq is None or scale_x is None or scale_y is None or scale_z is None or prefix is None or object_count is None or max_velocity is None or output_folder is None:
                error_string = error_string + 'Not all values specified.\n'
            # проверяем адекватность введённых значений
            if points_freq > 20:
                error_string = error_string + 'Points frequency cannot be more than 20 fps.\n'
            if colors_freq > 60:
                error_string = error_string + 'Colors frequency cannot be more than 60 fps.\n'
            if points_freq > colors_freq:
                error_string = error_string + 'Points frequency cannot be more than colors frequency.\n'
            if colors_freq % points_freq:
                error_string = error_string + 'Points and colors frequencies must be proportional.\n'
            if (not os.path.exists(template_path)):
                error_string = error_string + 'No *.lua quadrocopter script template specified.\n'
            if (not os.path.exists(output_folder)):
                error_string = error_string + 'Not valid output folder specified.\n'
            
            if len(error_string) > 0:
                gui.MessageDialog(error_string)
                return False
            else:
                print("\npoints_freq = {0}, colors_freq = {1}, scale_x = {2}, scale_y = {3}, scale_z = {4}, rotation = {5}, height_offset = {6}, prefix = {7}, N = {8}, max_vel = {11}\nTemplate: {9}\nOutput folder: {10}".format(points_freq, colors_freq, scale_x, scale_y, scale_z, rotation, height_offset, prefix, object_count, template_path, output_folder, max_velocity))
                # прокидываем значения в модуль для выполнения
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
                self.plugin.main() # наконец вызываем долгожданный метод
                self.plugin.createLuaScripts() # ну, и ещё один, в один не уложились :)
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
    
    animation_id = 1
    points_freq = 2.0
    colors_freq = 30.0
    time_step = 1.0 / colors_freq
    object_count = 10
    max_velocity = 5
    scale_x = 1.0
    scale_y = 1.0
    scale_z = 1.0
    lat = 0.0
    lon = 0.0
    rotation = 0
    height_offset = 4.0
    prefix = "drone_"
    output_folder = "."
    # инициализируются позже:
    module_path = None
    template_path = None
    
    STRUCT_FORMAT = "HhhHBBB" # единственная константа, которая не будет изменяться
    POINTS_FOLDER_NAME = "./points/"
    LUA_FOLDER_NAME = "./scripts/"
    BIN_FOLDER_NAME = "./bins/"
    
    def getPointsFolder(self):
        return os.path.dirname(self.output_folder + self.POINTS_FOLDER_NAME) + "/"
        
    def getLuaFolder(self):
        return os.path.dirname(self.output_folder + self.LUA_FOLDER_NAME) + "/"

    def getBinsFolder(self):
        return os.path.dirname(self.output_folder + self.BIN_FOLDER_NAME) + "/"
    
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
    
    def __init__(self, animation_id=None, points_freq=None, colors_freq=None, obj_number=None, base_name=None):
        if animation_id is not None:
            self.animation_id = animation_id
        if points_freq is not None:
            self.points_freq = points_freq
        if colors_freq is not None:
            self.colors_freq = colors_freq    
        if obj_number is not None:
            self.object_count = obj_number
        if base_name is not None:
            self.prefix = base_name 
        self.module_path = os.path.dirname(__file__) # папка, в которой хранится модуль, очень полезна
        self.template_path = self.module_path + "/c4d_animation.lua" #путь до шаблона также обязателен

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
                gui.MessageDialog("Object's name \"{0:s}\" doesn't exist".format(objectName))
                return
            else:
                objects.append(obj)
        return objects

    def getPositions(self, objects):
        vecPosition = []
        for obj in objects:
            vec = obj.GetAbsPos()
            vec.y += self.height_offset
            vecPosition.append(vec)
        return vecPosition
        
    def getActiveObjectName(self):
        active_object = self.doc.GetActiveObject()
        try:
            return active_object.GetName()
        except AttributeError:
            return None
    
    def main(self):
        doc = documents.GetActiveDocument()
        self.doc = doc
        max_time = doc.GetMaxTime().Get()
        self.time_step = 1/self.colors_freq
        max_time = (max_time // self.time_step + 2) * self.time_step
        max_points = int((max_time - self.time_step) / self.time_step)
        time = 0
        points_array = []
        data = [[] for i in range(self.object_count)]

        collisions_array = []
        velocities_array = []

        fps = doc.GetFps()

        shot_time = c4d.BaseTime(time)
        doc.SetTime(shot_time)
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_REDUCTION | c4d.DRAWFLAGS_NO_THREAD)

        objNames = self.getNames()
        objects = self.getObjects(objNames)
        prev_vecPosition = self.getPositions(objects)
        n = len(prev_vecPosition)
        excess_velocity_array = [self.max_velocity] * n
        excess_start_array = [0] * n
        excess_frames_array = [0] * n
        collision_distance_array = [ [self.min_distance] * n for _ in range(n)]
        collision_start_array = [ [0] * n for _ in range(n)]

        for i in range(self.object_count):
            s = '-- Time step is {0:.2f} s\n'\
                '-- Maximum number of points is {1}\n'\
                '-- [time]=cs, [x][y][z]=cm, [r][g][b]=0-255\n'\
                'local points  =  "'.format(self.time_step, max_points)
            points_array.append([s])

        while time <= max_time:
            shot_time = c4d.BaseTime(time)
            doc.SetTime(shot_time)
            c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_REDUCTION | c4d.DRAWFLAGS_NO_THREAD)            
            counter = 0
            for obj in objects:
                #Get color
                try:
                    objMaterial = obj.GetTag(Ttexture).GetMaterial()
                except AttributeError:
                    # print ("First object tag must be Material")
                    gui.MessageDialog("Didn't find object's ({0:s}) tag \"Material\"".format(obj.GetName()))
                    return
                vecRGB = objMaterial.GetAverageColor(c4d.CHANNEL_COLOR) # получаем RGB

                #Get position
                vecPosition = obj.GetAbsPos()

                # масштабирование пространственного вектора
                vecPosition.x = vecPosition.x * self.scale_x
                vecPosition.y = vecPosition.y * self.scale_y
                vecPosition.z = vecPosition.z * self.scale_z
                
                #поворот в пространстве вдоль оси OY (направлена вверх)
                rot_rad = self.rotation*math.pi/180
                x_temp = math.cos(rot_rad)*vecPosition.x - math.sin(rot_rad)*vecPosition.z
                z_temp = math.sin(rot_rad)*vecPosition.x + math.cos(rot_rad)*vecPosition.z
                vecPosition.x = x_temp
                vecPosition.z = z_temp
                
                # подъём сцены на некоторую высоту
                vecPosition.y = vecPosition.y + self.height_offset

                # Calculate velocity
                if self.max_velocity > 0:
                    if int(vecPosition.y) > (self.height_offset):
                        vel = pow((vecPosition.x - prev_vecPosition[counter].x) ** 2 + (vecPosition.y - prev_vecPosition[counter].y) ** 2 + (vecPosition.z - prev_vecPosition[counter].z) ** 2, 0.5)
                        vel = (vel / self.time_step) / 100
                        if vel > self.max_velocity:
                            excess_frames_array[counter] = 0
                            if excess_start_array[counter] == 0:
                                excess_start_array[counter] = time
                            if vel > excess_velocity_array[counter]:
                                excess_velocity_array[counter] = vel
                        elif excess_start_array[counter] != 0:
                            if excess_frames_array[counter] > int(self.colors_freq):
                                start_time = excess_start_array[counter]
                                end_time = time - excess_frames_array[counter]*self.time_step
                                s = "Velocity of\t{:03d}\tis up to\t{:.2f} m/s\tTime: {:.2f}-{:.2f} s\tFrames: {}-{}".format(counter, excess_velocity_array[counter], start_time, end_time, int(start_time*fps), int(end_time*fps))
                                velocities_array.append(s)
                                excess_start_array[counter] = 0
                                excess_frames_array[counter] = 0
                            else:
                                excess_frames_array[counter] += 1
                    if excess_start_array[counter] != 0 and (time + self.time_step) > max_time:
                        start_time = excess_start_array[counter]
                        end_time = time - excess_frames_array[counter]*self.time_step
                        s = "Velocity of\t{:03d}\tis up to\t{:.2f} m/s\tTime: {:.2f}-{:.2f} s\tFrames: {}-{}".format(counter, excess_velocity_array[counter], start_time, end_time, int(start_time*fps), int(end_time*fps))
                        velocities_array.append(s)
                        excess_start_array[counter] = 0
                        excess_frames_array[counter] = 0
                try:
                    s = struct.pack(self.STRUCT_FORMAT,
                                                int(time * 100),   #H
                                                int(vecPosition.x), #h
                                                int(vecPosition.z), #h
                                                int(vecPosition.y), #H
                                                int(vecRGB.x * 255), #B
                                                int(vecRGB.y * 255), #B
                                                int(vecRGB.z * 255)) #B
                except:
                    print("\n\nObject '{0}':\nTime = {1}\nx = {2}, y = {3}, z = {4}\nred = {5}, green = {6}, blue = {7}\n\n".format(
                                                obj.GetName(), #0
                                                int(time * 100), #1
                                                int(vecPosition.x), #2
                                                int(vecPosition.z), #3
                                                int(vecPosition.y), #4
                                                int(vecRGB.x * 255), #5
                                                int(vecRGB.y * 255), #6
                                                int(vecRGB.z * 255))) #7
                    gui.MessageDialog("Data out of format range.\n\nCheck console.")
                    raise
                if int(vecPosition.y) > (self.height_offset): # append if altitude greater than 0 in animation
                    s_xhex = binascii.hexlify(s)
                    points_array[counter].append(''.join([r'\x' + s_xhex[i:i+2] for i in range(0, len(s_xhex), 2)]))
                    data[counter].append([  time,
                                            vecPosition.x,
                                            vecPosition.z,
                                            vecPosition.y,
                                            int(vecRGB.x * 255),
                                            int(vecRGB.y * 255),
                                            int(vecRGB.z * 255)])
                prev_vecPosition[counter] = vecPosition
                counter += 1

            # Check distance
            if self.min_distance > 0:
                for j in range(n-1):
                    for k in range(j+1, n):
                        x1 = prev_vecPosition[j].x
                        y1 = prev_vecPosition[j].y
                        z1 = prev_vecPosition[j].z
                        x2 = prev_vecPosition[k].x
                        y2 = prev_vecPosition[k].y
                        z2 = prev_vecPosition[k].z
                        if int(y1) > (self.height_offset) and int(y2) > (self.height_offset):
                            distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2) / 100
                            if distance < self.min_distance:
                                if collision_start_array[j][k] == 0:
                                    collision_start_array[j][k] = time
                                if distance < collision_distance_array[j][k]:
                                    collision_distance_array[j][k] = distance
                            elif collision_start_array[j][k] != 0:
                                    start_time = collision_start_array[j][k]
                                    end_time = time - self.time_step
                                    collision_str = "Collision between:\t{:03d}\tand\t{:03d}\tMin distance: {:.2f} m\tTime: {:.2f}-{:.2f} s\tFrames: {}-{}".format(j, k, collision_distance_array[j][k], start_time, end_time, int(start_time*fps), int(end_time*fps))
                                    collisions_array.append(collision_str)
                                    collision_start_array[j][k] = 0
                                    collision_distance_array[j][k] = self.min_distance
                        if collision_start_array[j][k] != 0 and (time + self.time_step) > max_time:
                            start_time = collision_start_array[j][k]
                            end_time = time - self.time_step
                            collision_str = "Collision between:\t{:03d}\tand\t{:03d}\tMin distance: {:.2f} m\tTime: {:.2f}-{:.2f} s\tFrames: {}-{}".format(j, k, collision_distance_array[j][k], start_time, end_time, int(start_time*fps), int(end_time*fps))
                            collisions_array.append(collision_str)
                            collision_start_array[j][k] = 0
                            collision_distance_array[j][k] = self.min_distance
            time += self.time_step

        # Console check report
        print "\n"
        for s in collisions_array:
            print s
        print "\n"
        for s in velocities_array:
            print s
        msg_collision = "\nTOTAL NUMBER OF COLLISIONS: {}".format(len(collisions_array))
        msg_velocities = "\nTOTAL NUMBER OF VELOCITY EXCESS: {}".format(len(velocities_array))
        print msg_collision
        print msg_velocities
        if len(collisions_array) > 0:
            gui.MessageDialog(msg_collision)
        if len(velocities_array) > 0:
            gui.MessageDialog(msg_velocities)

        if not os.path.exists(os.path.dirname(self.getPointsFolder())):
            try:
                os.makedirs(os.path.dirname(self.getPointsFolder()))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        for i in range(self.object_count):
            fileName = self.getPointsFolder() + objNames[i] + ".lua"
            with open (fileName, "w") as f:
                for item in points_array[i]:
                    f.write(item)
                s = """"
local points_count = {0:d}
local str_format = \"{1:s}\"
local origin_lat = {2:f}
local origin_lon = {3:f}
--print ("t, s:\tx, m:\ty, m:\tz, m:\tr, byte:\tg, byte:\tb, byte:")
--for n = 0, {0:d} do
    --t, x, y, z, r, g, b, _ = string.unpack(str_format, points, 1 + n * string.packsize(str_format))
    --print (string.format("%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t\t%.2f\t\t%.2f\t\t", t/100, x/100, y/100, z/100, r/255, g/255, b/255))
--end\n""".format(len(points_array[i])-2, self.STRUCT_FORMAT, self.lat, self.lon)
                f.write(s)

        if not os.path.exists(os.path.dirname(self.getBinsFolder())):
            try:
                os.makedirs(os.path.dirname(self.getBinsFolder()))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        for i in range(self.object_count):
            points_count = len(points_array[i])-2
            freq_ratio = self.colors_freq/self.points_freq
            fileName = self.getBinsFolder() + objNames[i] + ".bin"
            with open (fileName, "wb") as f:
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
                TimeEnd = 0.0
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
                for n in range(0, points_count, int(freq_ratio)):
                    f.write(struct.pack('<fff', *[pos/100 for pos in data[i][n][1:4]]))
                    counter += 1

                if counter < 1800:
                    for _ in range(counter, 1800):
                        f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

                for n in range(points_count):
                    f.write(struct.pack('<BBB', *data[i][n][4:7]))

        gui.MessageDialog("Files are generated.\n\nPlease, check collisions in console output.\nMain menu->Script->Console")

    def createLuaScripts (self):
        objNames = self.getNames()

        if not os.path.exists(os.path.dirname(self.getLuaFolder())):
            try:
                os.makedirs(os.path.dirname(self.getLuaFolder()))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        for i in range(self.object_count):
            pointsFileName = self.getPointsFolder() + objNames[i] + ".lua"
            with open (pointsFileName, "r") as f_points, open (self.template_path, "r") as f_temp, open (self.getLuaFolder() + objNames[i] + ".lua", "w") as f:
                f.write(f_points.read())
                #f.write("\n")
                f.write(f_temp.read())
                
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