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
import socket

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
	TEXT_TIME_STEP= 1008, # Подпись. Временной шаг в секундах
	
	
    # This is the ID for the group that contains the task widgets.
    GROUP_TASKS = 2000,

    BUTTON_OPEN = 3000, # Идентификатор кнопки для открытия целевой папки для скриптов
	BUTTON_GENERATE = 3001, # Идентификатор кнопки для запуска генерации скриптов
	
	EDIT_OUTPUT_FOLDER = 4000, # Идентификатор текстового поля, в котором хранится путь до целевой папки
	EDIT_PREFIX = 4001, # Идентификатор текстового поля с префиксом объектов
	EDIT_OBJECT_COUNT = 4002, # Идентификатор текстового поля с количеством объектов
	EDIT_SCALE_GLOBAL = 4003, # Текстовое поле с глобальным пространственным масштабом
	EDIT_SCALE_X= 4004, # Текстовое поле с масштабом по x
	EDIT_SCALE_Y= 4005, # Текстовое поле с масштабом по y
	EDIT_SCALE_Z= 4006, # Текстовое поле с масштабом по z
	EDIT_ROTATION = 4007, # Текстовое поле, редактирующее поворот в градусах
	EDIT_TIME_STEP= 4008, # Текстовое поле с временным шагом в секундах
	
	CHECKBOX_GLOBAL_SCALE = 5000, #Чекбокс, регулирующий редактирование глобального масштаба

    # The following IDs are required for computing the IDs for
    # each widget that is required to display the task list.
    # We also want to be compatible in case we need future
    # changes so we reserve 10 widgets that are being used
    # for each row why we currently only use two.
    # The same IDs will be used to persistently store the tasks
    # in a c4d.BaseContainer.
    DYNAMIC_TASKS_START = 100000

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
        title_text = 'Todo In: %s' % current_doc.GetDocumentName()
        self.SetString(res.TEXT_DOCINFO, title_text)
		
        # получаем параметры из GUI-компонентов
        #self.SetFloat(res.EDIT_TIME_STEP, self.plugin.time_step, min = 1/30, step=1/30)
        self.SetString(res.EDIT_TIME_STEP, str(self.plugin.time_step))
        self.SetString(res.EDIT_SCALE_X, str(self.plugin.scale_x))
        self.SetString(res.EDIT_SCALE_Y, str(self.plugin.scale_y))
        self.SetString(res.EDIT_SCALE_Z, str(self.plugin.scale_z))
        self.SetString(res.EDIT_PREFIX, self.plugin.prefix)
        self.SetInt32(res.EDIT_ROTATION, self.plugin.rotation, min = 0, max = 360)
        self.SetInt32(res.EDIT_OBJECT_COUNT, self.plugin.object_count, min = 1)
        self.SetString(res.EDIT_OUTPUT_FOLDER, self.plugin.output_folder)

    def CreateLayout(self):
        self.SetTitle('Export to Pioneer Station')
		
        # Layout flag that will cause the widget to be scaled as much
        # possible in horizontal and vertical direction.
        BF_FULLFIT = c4d.BFH_CENTER | c4d.BFV_SCALEFIT
		
        # Create the main group that will encapsulate all of the
        # dialogs widgets. We can pass 0 if we don't want to supply
        # a specific ID.
        self.GroupBegin(0, BF_FULLFIT, cols=1, rows=0)
        self.GroupBorderSpace(4, 4, 4, 4)
		
        # This widget displays the active document's title.
        self.AddStaticText(res.TEXT_DOCINFO, c4d.BFH_SCALEFIT)
		
        self.LayoutFlushGroup(c4d.ID_SCROLLGROUP_STATUSBAR_EXTLEFT_GROUP)
		
		# начинаем группу-таблицу | текст | поле редактиирования |
        self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols = 2, rows = 6)
        global_initw = 250 # размер текстового поля должен быть одинаковым
		
		# Раздел Time Step
        self.AddStaticText(res.TEXT_TIME_STEP, c4d.BFH_RIGHT, initw=global_initw)
        self.SetString(res.TEXT_TIME_STEP, "Time step:")
		
        edit_time_step = self.AddEditText(res.EDIT_TIME_STEP, c4d.BFH_LEFT | c4d.BFH_SCALEFIT, initw = 200)
		# Конец раздела Time Step
		
		
		# Раздел Partial Scale Factor
        self.AddStaticText(res.TEXT_SCALE_PARTIAL, c4d.BFH_RIGHT, initw=global_initw)
        self.SetString(res.TEXT_SCALE_PARTIAL, "Partial scale factor (x, y, z):")
		
		# группа предназначена для объединения трёх редактируемых текстовых поля
        self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=3, rows=1)
        edit_scale_x = self.AddEditText(res.EDIT_SCALE_X, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        edit_scale_y = self.AddEditText(res.EDIT_SCALE_Y, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        edit_scale_z = self.AddEditText(res.EDIT_SCALE_Z, c4d.BFH_LEFT | c4d.BFH_SCALEFIT)
        self.GroupEnd()
	    # Конец раздела Partial Scale Factor
		
		# Раздел Rotate
        self.AddStaticText(res.TEXT_ROTATION, c4d.BFH_RIGHT, initw=global_initw)
        self.SetString(res.TEXT_ROTATION, "Rotation:")
		
        edit_rotate = self.AddEditNumberArrows(res.EDIT_ROTATION, c4d.BFH_LEFT | c4d.BFH_SCALEFIT, initw = 200)
	    # Конец раздела Rotate
		
		# Раздел Prefix
        self.AddStaticText(res.TEXT_PREFIX, c4d.BFH_RIGHT, initw=global_initw)
        self.SetString(res.TEXT_PREFIX, "Prefix:")
		
        edit_prefix = self.AddEditText(res.EDIT_PREFIX, c4d.BFH_LEFT | c4d.BFH_SCALEFIT, initw = 200)
		# Конец раздела Prefix
		
		# Раздел Object count
        self.AddStaticText(res.TEXT_OBJECT_COUNT, c4d.BFH_RIGHT, initw=global_initw)
        self.SetString(res.TEXT_OBJECT_COUNT, "Object count:")
		
        edit_object_count = self.AddEditNumberArrows(res.EDIT_OBJECT_COUNT, c4d.BFH_LEFT | c4d.BFH_SCALEFIT, initw = 200)
		# Конец раздела Object count
		
		
		# Раздел Output Folder
        self.AddStaticText(res.TEXT_OUTPUT_FOLDER, c4d.BFH_RIGHT, initw=global_initw)
        self.SetString(res.TEXT_OUTPUT_FOLDER, "Output folder:")
		
		# группа предназначена для группировки нередактируемого поля и кнопки "открыть"
        self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_TOP, cols=0, rows=1)
        edit_output_folder = self.AddEditText(res.EDIT_OUTPUT_FOLDER, c4d.BFH_LEFT | c4d.BFH_SCALEFIT, initw = 200)
        self.Enable(edit_output_folder, False) #выключаем редактирование поля (от греха подальше)
        self.AddButton(res.BUTTON_OPEN, c4d.BFH_RIGHT, name="open")
        self.GroupEnd()
		# Конец раздела Output Folder
		
        self.GroupEnd() # конец группы-таблицы
		
		# наконец добавляем кнопку генерации скриптов
        self.AddButton(res.BUTTON_GENERATE, c4d.BFH_CENTER, name="Generate")
        
        self.Refresh()
		
        self.GroupEnd()
        self.LayoutChanged(c4d.ID_SCROLLGROUP_STATUSBAR_EXTLEFT_GROUP)
        return True
        
    def Command(self, param, bc):
	    # если тыкнули в кнопку "открыть файл"
        if param == res.BUTTON_OPEN:
            filename = c4d.storage.LoadDialog(title="Choose folder to store files", flags = c4d.FILESELECT_DIRECTORY)
            if not filename is None:
                self.output_folder = filename
                self.SetString(res.EDIT_OUTPUT_FOLDER, filename)
                return True
            else:
                return False
        elif param == res.BUTTON_GENERATE:
            # получаем параметры из GUI-компонентов
            error_string = ''
            try:
                time_step = float(self.GetString(res.EDIT_TIME_STEP))
                scale_x = float(self.GetString(res.EDIT_SCALE_X))
                scale_y = float(self.GetString(res.EDIT_SCALE_Y))
                scale_z = float(self.GetString(res.EDIT_SCALE_Z))
            except:
                error_string = error_string + 'Invalid floating point number'
                pass
            prefix = self.GetString(res.EDIT_PREFIX)
            object_count =  self.GetInt32(res.EDIT_OBJECT_COUNT)
            rotation =  self.GetInt32(res.EDIT_ROTATION)
            output_folder = self.GetString(res.EDIT_OUTPUT_FOLDER)
            
			# проверяем, что параметры прочитались
            if time_step is None or scale_x is None or scale_y is None or scale_z is None or prefix is None or object_count is None or output_folder is None:
                error_string = error_string + 'Not all values specified.\n'
			# проверяем адекватность введённых значений
            if (time_step < 1.0/30): # быстрее 30 кадров в секунду нельзя
                error_string = error_string + 'Time step cannot be faster, than 30 fps.\n'
            if (object_count <= 0): # хотя бы один объект необходим. 
                #0 объектов, формально, допустимы, но без оповещения об ошибке может вызвать когнитивный диссонанс у пользователя
                error_string = error_string + 'There should be at least one object to export code.\n'
            if (not os.path.exists(output_folder)):
                error_string = error_string + 'Not valid output folder specified.\n'
            
            if len(error_string) > 0: # если строка ошибок не пуста, значит есть проблемы. Вывести их.
                gui.MessageDialog(error_string)
                return False
            else:
                #print("time_step={0}, scale_x={1}, scale_y={2}, scale_z={3}, prefix={4}, N={5}, folder={6}".format(time_step, scale_x, scale_y, scale_z, prefix, object_count, output_folder))
                self.plugin.time_step = time_step
                self.plugin.scale_x = scale_x
                self.plugin.scale_y = scale_y
                self.plugin.scale_z = scale_z
                self.plugin.prefix = prefix
                self.plugin.rotation = rotation
                self.plugin.object_count = object_count
                self.plugin.output_folder = output_folder
                self.plugin.main() # наконец вызываем долгожданный метод
                self.plugin.createLuaScripts() # ну, и ещё один, в один не уложились :)
                self.plugin.uploadScriptToPioneerStation() # загрузку в PioneerStation стоит вынести на отдельную кнопку (?)
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
	
    time_step = 0.5
    object_count = 3
    scale_x = 1.0
    scale_y = 1.0
    scale_z = 1.0
    rotation = 0
    prefix = "drone_"
    output_folder = "."
    drone_index = None # динамическая переменная с определением активного робота
	
    STRUCT_FORMAT = "iiiHHBB" # единственная константа, которая не будет изменяться
    FOLDER_NAME = "./points/"
    LUA_FOLDER_NAME = "./scripts/"
	
    def getPointsFolder(self):
        return os.path.dirname(self.output_folder + self.FOLDER_NAME) + "/"
		
    def getLuaFolder(self):
        return os.path.dirname(self.output_folder + self.LUA_FOLDER_NAME) + "/"
    
    def Register(self):
        help_string = 'Geoscan capture plugin: convert Cinema 4D' \
                      'scene into drone code.'
					  
		# подгружаем иконку для плагина, если это возможно
        ico = c4d.bitmaps.BaseBitmap()
        if ico.InitWith(self.module_path + "\\geoscan.ico")[0] != c4d.IMAGERESULT_OK:
            ico = None # если не вышло подгрузить, иконку не передаём

        return c4d.plugins.RegisterCommandPlugin(
                PLUGIN_ID,                   # The Plugin ID, obviously
                "Pioneer capture",  # The name of the plugin
                c4d.PLUGINFLAG_COMMAND_HOTKEY,    # Sort of options
                ico,                        # Icon, Geoscan here
                help_string,                 # The help text for the command
                self,                        # The plugin implementation
        )
    
    def __init__(self, time_step=None, obj_number=None, base_name=None):
        if not time_step is None:
            self.time_step = time_step
        if not obj_number is None:
            self.object_count = obj_number
        if not base_name is None:
            self.prefix = base_name
        self.module_path = os.path.dirname(__file__) # папка, в которой хранится модуль, очень полезна

    def getNames (self):
        names = []
        activeObjectName = self.getActiveObjectName()
        for indexName in range(self.object_count):
            name = self.prefix + "{0:d}".format(indexName)
            names.append(name)
            if name == activeObjectName:
                self.drone_index = indexName # запоминаем имя активного дрона
                print("Current drone #" + str(indexName))
            
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
        
    def getActiveObjectName(self):
        active_object = self.doc.GetActiveObject()
        try:
            return active_object.GetName()
        except AttributeError:
            return None
    
    def uploadScriptToPioneerStation(self):
        if self.drone_index is None:
            return
        # автоматически подгружаем скрипт в PioneerStation, если удастся
        objNames = self.getNames()
        print("Autoloading script #" + str(self.drone_index))
        f = open (self.getLuaFolder() + objNames[self.drone_index] + ".lua", "rb")

        sock = socket.socket()
        try:
            sock.connect(('127.0.0.1', 8080))
        except:
            print("No pioneer station network service found.")
            return
        header = 'POST /pioneer/v0.1/upload HTTP/1.1\r\nContent-Type: text/plain\r\nContent-Length: {0}\r\nConnection: Keep-Alive\r\nAccept-Encoding: gzip, deflate\r\nAccept-Language: ru-RU,en,*\r\nUser-Agent: Mozilla/5.0\r\nHost: 127.0.0.1:8080\r\n\r\n'


        source_code = f.read()

        header = header.format(str(len(source_code))).encode('ascii')

        sock.send(header)
        sock.send(source_code)

        resp = sock.recv(1024)
        print(resp)

        sock.close()
        

    def main(self):
        doc = documents.GetActiveDocument()
        self.doc = doc
        maxTime = doc.GetMaxTime().Get()
        objNames = self.getNames()
        objects = self.getObjects(objNames)

        time = 0
        points_array = []
        for i in range(self.object_count):
            s = '-- Time step is {0:.2f} s\n'\
                '-- [time]=ms, [x][y][z]=cm, [r][g][b]=0-255\n'\
                'local points  =  "'.format(self.time_step, self.object_count, self.STRUCT_FORMAT)
            points_array.append([s])

        while time <= maxTime:
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
                    gui.MessageDialog("Didn't find object's ({0:s}) tag \"Material\"".format(obj))
                    return
                vecRGB = objMaterial.GetAverageColor(c4d.CHANNEL_COLOR) # получаем RGB
                # это ненормированный вектор RGB, исправляем ситуацию. Норма подразумевается равномерной
                intensity = max(vecRGB.x, vecRGB.y, vecRGB.z)
                vecRGB = vecRGB / intensity
                vecHSV = c4d.utils.RGBToHSV(vecRGB) # конвертируем RGB в HSV. Все значения в интервале [0, 1]
                # домножаем также на intensity текущий цвет. Разработчики сцен смогут повлиять на яркость коптера
                vecHSV.z = vecHSV.z * intensity
                if (int(vecHSV.z * 100) > 255): # верхний предел для того, чтобы всё влезло в байт
                    vecHSV.z = 2.55
					
                #Get position
                vecPosition = obj.GetAbsPos()
                # масштабирование пространственного вектора
                vecPosition.x = vecPosition.x*self.scale_x
                vecPosition.y = vecPosition.y*self.scale_y
                vecPosition.z = vecPosition.z*self.scale_z
				
				#поворот в пространстве вдоль оси OY (направлена вверх)
                rot_rad = self.rotation*math.pi/180
                x_temp = math.cos(rot_rad)*vecPosition.x - math.sin(rot_rad)*vecPosition.z
                z_temp = math.sin(rot_rad)*vecPosition.x + math.cos(rot_rad)*vecPosition.z
                vecPosition.x = x_temp
                vecPosition.z = z_temp
                
                s = struct.pack(self.STRUCT_FORMAT,  
                                                int(time * 1000),   #i 
                                                int(vecPosition.x), #i
                                                int(vecPosition.z), #i
                                                int(vecPosition.y), #H
                                                int(vecHSV.x * 360), #H
                                                int(vecHSV.y * 100), #B
                                                int(vecHSV.z * 100)) #B
                # print s
                s_xhex = binascii.hexlify(s)
                points_array[counter].append(''.join([r'\x' + s_xhex[i:i+2] for i in range(0, len(s_xhex), 2)]))
                counter = counter + 1
            time += self.time_step

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
--for n = 0, {0:d} do
    --t, x, y, z, r, g, b, _ = string.unpack(str_format, points, 1 + n * string.packsize(str_format))
    --print (t/1000, x/100, y/100, z/100, r/255, g/255, b/255)
--end """.format(int((time - self.time_step)/self.time_step), self.STRUCT_FORMAT)
                f.write(s)
        gui.MessageDialog("Files generated!")

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
            with open (pointsFileName, "r") as f_points, open (self.module_path + "/c4d_animation.lua", "r") as f_temp, open (self.getLuaFolder() + objNames[i] + ".lua", "w") as f:
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