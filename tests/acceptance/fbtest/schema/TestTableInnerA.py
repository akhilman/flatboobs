# automatically generated by the FlatBuffers compiler, do not modify

# namespace: schema

import flatbuffers

class TestTableInnerA(object):
    __slots__ = ['_tab']

    @classmethod
    def GetRootAsTestTableInnerA(cls, buf, offset):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = TestTableInnerA()
        x.Init(buf, n + offset)
        return x

    # TestTableInnerA
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

    # TestTableInnerA
    def ValueA(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Uint8Flags, o + self._tab.Pos)
        return 0

    # TestTableInnerA
    def ValueB(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Uint8Flags, o + self._tab.Pos)
        return 0

def TestTableInnerAStart(builder): builder.StartObject(2)
def TestTableInnerAAddValueA(builder, valueA): builder.PrependUint8Slot(0, valueA, 0)
def TestTableInnerAAddValueB(builder, valueB): builder.PrependUint8Slot(1, valueB, 0)
def TestTableInnerAEnd(builder): return builder.EndObject()