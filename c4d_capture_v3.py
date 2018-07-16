#!/usr/bin/python
# -*- coding: utf-8  -*-

import c4d
from c4d import Ttexture
from c4d import gui, documents
import os
import errno
import struct
import binascii
import socket


class c4d_capture:
    PERIOD = 0.5
    OBJS_NUMBER = 3
    BASE_NAME = "drone_"
    STRUCT_FORMAT = "iiiHHBB"
    FOLDER_NAME = "./points/"
    LUA_FOLDER_NAME = "./scripts/"
    DRONE_INDEX = None
    
    
    def __init__(self, period=None, obj_number=None, base_name=None):
        if not period is None:
            self.PERIOD = period
        if not obj_number is None:
            self.OBJS_NUMBER = obj_number
        if not base_name is None:
            self.BASE_NAME = base_name

    def getNames (self):
        names = []
        activeObjectName = self.getActiveObjectName()
        for indexName in range(self.OBJS_NUMBER):
            name = self.BASE_NAME + "{0:d}".format(indexName)
            names.append(name)
            if name == activeObjectName:
                self.DRONE_INDEX = indexName # запоминаем имя активного дрона
                print("Current drone #" + str(indexName))
            
        return names

    def getObjects(self, objectNames):
        objects = []
        for objectName in objectNames:
            obj = doc.SearchObject(objectName)
            if obj == None:
                #print ("Object {0:s} doesn't exist".format(objectName))
                gui.MessageDialog("Object's name \"{0:s}\" doesn't exist".format(objectName))
                return
            else:
                objects.append(obj)
        return objects
        
    def getActiveObjectName(self):
        active_object = doc.GetActiveObject()
        try:
            return active_object.GetName()
        except AttributeError:
            return None
    
    def uploadScriptToPioneerStation(self):
        if self.DRONE_INDEX is None:
            return
        # автоматически подгружаем скрипт в PioneerStation, если удастся
        objNames = self.getNames()
        print("Autoloading script #" + str(self.DRONE_INDEX))
        f = open (self.LUA_FOLDER_NAME + objNames[self.DRONE_INDEX] + ".lua", "rb")

        sock = socket.socket()
        sock.connect(('127.0.0.1', 8080))
        header = 'POST /pioneer/v0.1/upload HTTP/1.1\r\nContent-Type: text/plain\r\nContent-Length: {0}\r\nConnection: Keep-Alive\r\nAccept-Encoding: gzip, deflate\r\nAccept-Language: ru-RU,en,*\r\nUser-Agent: Mozilla/5.0\r\nHost: 127.0.0.1:8080\r\n\r\n'


        source_code = f.read()

        header = header.format(str(len(source_code))).encode('ascii')

        sock.send(header)
        sock.send(source_code)

        resp = sock.recv(1024)
        print(resp)

        #data = sock.recv(1024)
        sock.close()
        

    def main(self):
        #doc = documents.GetActiveDocument()
        maxTime = doc.GetMaxTime().Get()
        objNames = self.getNames()
        objects = self.getObjects(objNames)

        time = 0
        points_array = []
        for i in range(self.OBJS_NUMBER):
            s = """ 
-- Time step is {0:.2f} s
-- [time]=ms, [x][y][z]=cm, [r][g][b]=0-255
local points  =  '""".format(self.PERIOD, self.OBJS_NUMBER, self.STRUCT_FORMAT)
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
                #print("RGB before:")
                #print(vecRGB.x, vecRGB.y, vecRGB.z)
                # это ненормированный вектор RGB, исправляем ситуацию. Норма подразумевается равномерной
                intensity = max(vecRGB.x, vecRGB.y, vecRGB.z)
                vecRGB = vecRGB / intensity
                #print("RGB arter:")
                #print(vecRGB.x, vecRGB.y, vecRGB.z)
                vecHSV = c4d.utils.RGBToHSV(vecRGB) # конвертируем RGB в HSV. Все значения в интервале [0, 1]
                # домножаем также на intensity текущий цвет. Разработчики сцен смогут повлиять на яркость коптера
                vecHSV.z = vecHSV.z * intensity
                if (int(vecHSV.z * 100) > 255): # верхний предел для того, чтобы всё влезло в байт
                    vecHSV.z = 2.55
                #print("HSV:")
                print(vecHSV.x, vecHSV.y, vecHSV.z)
                
                #Get position
                vecPosition = obj.GetAbsPos()
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
            time += self.PERIOD

        if not os.path.exists(os.path.dirname(self.FOLDER_NAME)):
            try:
                os.makedirs(os.path.dirname(self.FOLDER_NAME))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        for i in range(self.OBJS_NUMBER):
            fileName = self.FOLDER_NAME + objNames[i] + ".lua"
            with open (fileName, "w") as f:
                for item in points_array[i]:
                    f.write(item)
                s = """'
local points_count = {0:d}
local str_format = \"{1:s}\"
--for n = 0, {0:d} do
    --x, y, z, t, r, g, b, _ = string.unpack(str_format, points, 1 + n * string.packsize(str_format))
    --print (t/1000, x/100, y/100, z/100, r/255, g/255, b/255)
--end """.format(int((time - self.PERIOD)/self.PERIOD), self.STRUCT_FORMAT)
                f.write(s)
        gui.MessageDialog("Files generated!")

    def createLuaScripts (self):
        objNames = self.getNames()

        if not os.path.exists(os.path.dirname(self.LUA_FOLDER_NAME)):
            try:
                os.makedirs(os.path.dirname(self.LUA_FOLDER_NAME))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        for i in range(self.OBJS_NUMBER):
            pointsFileName = self.FOLDER_NAME + objNames[i] + ".lua"
            with open (pointsFileName, "r") as f_points, open ("./template/c4d_animation.lua", "r") as f_temp, open (self.LUA_FOLDER_NAME + objNames[i] + ".lua", "w") as f:
                f.write(f_points.read())
                #f.write("\n")
                f.write(f_temp.read())


if __name__=="__main__":
    capture = c4d_capture(0.5, 3)
    capture.main()
    capture.createLuaScripts()
    capture.uploadScriptToPioneerStation() # if object selected, uploads to pioneer station sw