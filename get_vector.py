import c4d
from c4d import gui, documents
import os
import errno


PERIOD = 0.5
MAX_INDEX = 40
BASE_NAME = "Sphere "

def getNames ():
    names = []
    for indexName in range(MAX_INDEX):
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
    pos = []
    for i in range(MAX_INDEX):
        pos.append([])

    while time <= maxTime:
        shot_time = c4d.BaseTime(time)
        doc.SetTime(shot_time)
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_REDUCTION | c4d.DRAWFLAGS_NO_THREAD)
        counter = 0
        for obj in objects:
            #Get color
            try:
                objMaterial = obj.GetFirstTag().GetMaterial()
            except AttributeError:
                # print ("First object tag must be Material")
                gui.MessageDialog("First object's ({0:s}) tag must be \"Material\"".format(obj))
                return
            vecColor = objMaterial.GetAverageColor(c4d.CHANNEL_COLOR)
            #Get position
            vecPosition = obj.GetAbsPos()
            s = "t = {0:.2f} \tx = {1:.2f} \ty = {2:.2f} \tz = {3:.2f} \tr = {4:.2f} \tg = {5:.2f} \tb = {6:.2f} \n".format(time, vecPosition.x, vecPosition.y, vecPosition.z, vecColor.x, vecColor.y, vecColor.z)
            #print s
            pos[counter].append(s)
            counter += 1
        time += PERIOD

    folderName = "./coordinates/"
    if not os.path.exists(os.path.dirname(folderName)):
        try:
            os.makedirs(os.path.dirname(folderName))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    for i in range(MAX_INDEX):
        fileName = folderName + objNames[i] + ".txt"
        with open (fileName, "w") as f:
            for item in pos[i]:
                f.write("%s" % item)

    gui.MessageDialog("Files generated!")
            



if __name__=='__main__':
    main()