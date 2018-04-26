import c4d
from c4d import gui
def main():

    obj=doc.GetActiveObject();
    vec = obj.GetAbsPos()

    print "Vector: x =", vec.x, "y =", vec.y, "z =", vec.z

if __name__=='__main__':
    main()