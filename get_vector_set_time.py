import c4d
from c4d import gui, documents
import time



def main():

    obj = doc.SearchObject("Sphere 2")
    i = 0
    while i < 15:
        shot_time = c4d.BaseTime(i)
        documents.SetDocumentTime(doc, shot_time)
        vec = obj.GetAbsPos()
        s = "t = {0:.2f} \tx = {1:.2f} \ty = {2:.2f} \tz = {3:.2f}\n".format(i, vec.x, vec.y, vec.z)
        print s
        i = i + 1
    


if __name__=='__main__':
    main()