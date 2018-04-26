import c4d
from c4d import gui, documents


MAX_TIME = 40
PERIOD = 0.5

def main():
    
    def gototime():
        doc = documents.GetActiveDocument()
        #maxTime = doc.GetMaxTime()
        #print maxTime
        print ("----------------")
        obj = doc.SearchObject("Sphere 1")
        i = 0
        with open ("coordinates.txt", "w") as f:
            while i < MAX_TIME:
                shot_time = c4d.BaseTime(i)
                #print shot_time.Get()
                #res = False
                doc.SetTime(shot_time)
                #c4d.EventAdd(c4d.EVENT_FORCEREDRAW)
                c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_REDUCTION)
                vec = obj.GetAbsPos()
                s = "t = {0:.2f} \tx = {1:.2f} \ty = {2:.2f} \tz = {3:.2f}\n".format(i, vec.x, vec.y, vec.z)
                print s
                f.write(s)
                i += PERIOD
                
    gototime()
    


if __name__=='__main__':
    main()