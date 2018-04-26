import c4d
from c4d import gui, documents


PERIOD = 1
MAX_INDEX_NAME = 40

def getNames (baseName):
    names = []
    for indexName in range(MAX_INDEX_NAME):
        name = baseName + "{0:d}".format(indexName)
        names.append(name)
    return names

def getObjects(objectNames):
    objects = []
    for objectName in objectNames:
        obj = doc.SearchObject(objectName)
        if obj == None:
            print ("Object {0:s} doesn't exist".format(objectName))
            return
        else:
            objects.append(obj)
    return objects

def main():
    baseObjName = "Sphere "

    #doc = documents.GetActiveDocument()
    maxTime = doc.GetMaxTime().Get()
    objNames = getNames(baseObjName)
    objects = getObjects(objNames)

    # try:
    #     objMaterial = obj.GetFirstTag().GetMaterial()
    # except AttributeError:
    #     print ("First object tag must be Material")
    #     return
    # objColor = objMaterial.GetAverageColor(c4d.CHANNEL_COLOR)
    #print objColor

    time = 0
    pos = []
    for i in range(MAX_INDEX_NAME):
        pos.append([])

    while time <= maxTime:
        shot_time = c4d.BaseTime(time)
        doc.SetTime(shot_time)
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_REDUCTION)
        counter = 0
        for obj in objects:
            vec = obj.GetAbsPos()
            s = "t = {0:.2f} \tx = {1:.2f} \ty = {2:.2f} \tz = {3:.2f}\n".format(time, vec.x, vec.y, vec.z)
            #print s
            pos[counter].append(s)
            counter += 1
        time += PERIOD

    for i in range(MAX_INDEX_NAME):
        fileName = objNames[i] + ".txt"
        with open (fileName, "w") as f:
            for item in pos[i]:
                f.write("%s" % item)
            



if __name__=='__main__':
    main()