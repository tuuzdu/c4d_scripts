#!/usr/bin/python
# -*- coding: utf-8  -*-

import c4d
from c4d import Ttexture
from c4d import gui, documents
import os
import errno
import struct
import binascii

PERIOD = 0.5
OBJS_NUMBER = 10
BASE_NAME = "drone_"
STRUCT_FORMAT = "iiiHBBB"


def getNames ():
    names = []
    for indexName in range(OBJS_NUMBER):
        name = BASE_NAME + "{0:d}".format(indexName)
        names.append(name)
    return names

def getObjects(objectNames):
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

def main():
    #doc = documents.GetActiveDocument()
    maxTime = doc.GetMaxTime().Get()
    objNames = getNames()
    objects = getObjects(objNames)

    time = 0
    points_array = []
    for i in range(OBJS_NUMBER):
        s = """ -- Time step is {0:.2f} s\n
                -- [time]=ms, [x][y][z]=cm, [r][g][b]=0-255\n
                local points_count = {1:d}\n
                local str_format = \"{2:s}\"\n
                local points  =  \"""".format(PERIOD, OBJS_NUMBER, STRUCT_FORMAT)
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
            vecColor = objMaterial.GetAverageColor(c4d.CHANNEL_COLOR)
            #Get position
            vecPosition = obj.GetAbsPos()
            s = struct.pack(STRUCT_FORMAT,  int(time * 1000), 
                                            int(vecPosition.x), 
                                            int(vecPosition.z), 
                                            int(vecPosition.y), 
                                            int(vecColor.x * 255), 
                                            int(vecColor.y * 255), 
                                            int(vecColor.z * 255))
            # print s
            s_xhex = binascii.hexlify(s)
            points_array[counter].append(''.join([r'\x' + s_xhex[i:i+2] for i in range(0, len(s_xhex), 2)]))
            counter += 1
        time += PERIOD

    folderName = "./points/"
    if not os.path.exists(os.path.dirname(folderName)):
        try:
            os.makedirs(os.path.dirname(folderName))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    for i in range(OBJS_NUMBER):
        fileName = folderName + objNames[i] + ".lua"
        with open (fileName, "w") as f:
            for item in points_array[i]:
                f.write(item)
            # f.write("\"\n")
            s = """ \"\n
                    --for n = 0, {:d} do\n\t
                        --t, x, y, z, r, g, b, _ = string.unpack('iiiHBBB', points, 1 + n * string.packsize('iiiHBBB'))\n\t
                        --print (t/1000, x/100, y/100, z/100, r/255, g/255, b/255)\n
                    --end""".format(int((time - PERIOD)/PERIOD))
            f.write(s)

    gui.MessageDialog("Files generated!")
            

if __name__=="__main__":
    main()