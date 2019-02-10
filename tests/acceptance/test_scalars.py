import flatbuffers
import pytest

from fbtest.schema import TestScalars
from flatboobs.utils import hexdump


@pytest.fixture
def data():
    return {
        'int_8': -8,
        'int_16': -1616,
        'int_32': -323232,
        'int_64': -6464646464,
        'uint_8': 8,
        'uint_16': 1616,
        'uint_32': 323232,
        'uint_64': 6464646464,
        'float_32': 32e32,
        'float_64': 64e64,
        'bool_true': True,
        'bool_false': False,
    }


def flatbuffers_pack(data):

    builder = flatbuffers.Builder(1024)
    TestScalars.TestScalarsStart(builder)

    TestScalars.TestScalarsAddInt8(builder, data['int_8'])
    TestScalars.TestScalarsAddInt16(builder, data['int_16'])
    TestScalars.TestScalarsAddInt32(builder, data['int_32'])
    TestScalars.TestScalarsAddInt64(builder, data['int_64'])

    TestScalars.TestScalarsAddUint8(builder, data['uint_8'])
    TestScalars.TestScalarsAddUint16(builder, data['uint_16'])
    TestScalars.TestScalarsAddUint32(builder, data['uint_32'])
    TestScalars.TestScalarsAddUint64(builder, data['uint_64'])

    TestScalars.TestScalarsAddFloat32(builder, data['float_32'])
    TestScalars.TestScalarsAddFloat64(builder, data['float_64'])

    TestScalars.TestScalarsAddBoolTrue(builder, data['bool_true'])
    TestScalars.TestScalarsAddBoolFalse(builder, data['bool_false'])

    root = TestScalars.TestScalarsEnd(builder)
    builder.Finish(root)

    return builder.Output()


def flatbuffers_unpack(buffer):
    return TestScalars.TestScalars.GetRootAsTestScalars(buffer, 0)


def test_unpack(registry, data):

    buffer = flatbuffers_pack(data)

    print('size', len(buffer))
    print(hexdump(buffer))

    table = registry.unpackb(buffer, root_type='TestScalars')

    assert len(table) == len(data)
    assert frozenset(table) == frozenset(data)
    assert frozenset(table.keys()) == frozenset(data.keys())

    for k in data.keys():
        if 'float' in k:
            assert table[k] == pytest.approx(data[k])
        else:
            assert table[k] == data[k]

    for res, ref in zip(sorted(table.items()), sorted(data.items())):
        assert res[0] == ref[0]
        assert res[1] == pytest.approx(ref[1])


# @pytest.mark.skip(reason="TODO")
def test_pack(registry, data):

    table = registry.new(type_name='TestScalars')
    table = table.evolve(**data)

    buffer = table.packb()

    print('size', len(buffer))
    print(hexdump(buffer))

    res = flatbuffers_unpack(buffer)

    assert res.Int8() == data['int_8']
    assert res.Int16() == data['int_16']
    assert res.Int32() == data['int_32']
    assert res.Int64() == data['int_64']

    assert res.Uint8() == data['uint_8']
    assert res.Uint16() == data['uint_16']
    assert res.Uint32() == data['uint_32']
    assert res.Uint64() == data['uint_64']

    assert res.Float32() == pytest.approx(data['float_32'])
    assert res.Float64() == pytest.approx(data['float_64'])

    assert res.BoolTrue() == data['bool_true']
    assert res.BoolFalse() == data['bool_false']


def test_bad_values(registry):

    table = registry.new(type_name='TestScalars')

    with pytest.raises(ValueError):
        table.evolve(float_32='hi there')

    with pytest.raises(ValueError):
        table.evolve(int_8=1 << 32)

    with pytest.raises(ValueError):
        table.evolve(uint_64=-1)
