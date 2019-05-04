import inspect, warnings, json
import global_accessor as ga
from PySide2 import QtCore


class UCoreUtils:

    @staticmethod
    def get_class_that_defined_method(meth):
        if inspect.ismethod(meth):
            for cls in inspect.getmro(meth.__self__.__class__):
                if cls.__dict__.get(meth.__name__) is meth:
                    return cls
            meth = meth.__func__  # fallback to __qualname__ parsing
        if inspect.isfunction(meth):
            cls = getattr(inspect.getmodule(meth),
                          meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
            if isinstance(cls, type):
                return cls

        return getattr(meth, '__objclass__', None)  # handle special descriptor objects

    @staticmethod
    def createPointerBoundingBox(pointerPos, bbSize):
        """
        generate a bounding box around the pointer.
        :param pointerPos: Pointer position.
        :type  pointerPos: QPoint.
        :param bbSize: Width and Height of the bounding box.
        :type  bbSize: Int.
        """
        # Create pointer's bounding box.
        point = pointerPos

        mbbPos = point
        point.setX(point.x() - bbSize / 2)
        point.setY(point.y() - bbSize / 2)

        size = QtCore.QSize(bbSize, bbSize)
        bb = QtCore.QRect(mbbPos, size)
        bb = QtCore.QRectF(bb)

        return bb

    @staticmethod
    def findBlock(s: str, frm: int = 0, dlmIn='{', dlmOut='}'):
        i = s.find(dlmIn, frm) + 1
        j = s.find(dlmOut, frm)

        return [i, j, s[i:j]]

    @staticmethod
    def checkBases(cls, stype, itMax=10):
        if isinstance(cls, type):
            if stype in cls.__bases__:
                return True

            else:
                for base in cls.__bases__:
                    if stype in base.__bases__:
                        return True
                    else:
                        itMax -= 1
                        return UCoreUtils.checkBases(base, stype, itMax)
        else:
            return False


    @staticmethod
    def findFmtArgs(s: str, frm: int = 0, dlmIn='{', dlmOut='}'):
        def check(v):
            return v[0] != -1 and v[1] != -1

        res = []
        i = frm
        while check(UCoreUtils.findBlock(s, i, dlmIn, dlmOut)):
            r = UCoreUtils.findBlock(s, i, dlmIn, dlmOut)
            print(i)
            res.append(r[2])
            i = r[1] + 1

        return res

    @staticmethod
    def getAppPath():
        return ga.getInstanceByName("APPLICATION").path

    @staticmethod
    def parsePath(p):
        r = p.replace("$APP", UCoreUtils.getAppPath())
        # ...

        return r

    @staticmethod
    def getMainConfig():
        p = UCoreUtils.getAppPath()
        with open("%s\\NodeProcess.config" % p, 'r') as f:
            data = json.load(f)

        return data
