import flatbuffers
import pytest

from fbtest.schema import TestStruct, TestStructStruct, TestStructEnum
from flatboobs.utils import asnative, hexdump


@pytest.fixture
def data():
    return {
        'foo': 0x123,
        'value': {
            'a': 0xEE,
            'b': 9.99,
            'e': TestStructEnum.TestStructEnum.Bar
        },
        'bar': 0xabc
    }


def flatbuffers_pack(data):

    builder = flatbuffers.Builder(1024)

    TestStruct.TestStructStart(builder)
    TestStruct.TestStructAddFoo(builder, data['foo'])
    offset = TestStructStruct.CreateTestStructStruct(
        builder, data['value']['a'], data['value']['b'], data['value']['e'])
    TestStruct.TestStructAddValue(builder, offset)
    TestStruct.TestStructAddBar(builder, data['bar'])
    root = TestStruct.TestStructEnd(builder)

    builder.Finish(root)

    return builder.Output()


def flatbuffers_unpack(buffer):
    return TestStruct.TestStruct.GetRootAsTestStruct(buffer, 0)


def test_unpack(serializer, data):

    buffer = flatbuffers_pack(data)

    print('size', len(buffer))
    print(hexdump(buffer))

    struct = serializer.unpackb('TestStruct', buffer)

    result = asnative(struct)

    from pprint import pprint
    pprint(result)

    assert result.keys() == data.keys()
    for outer_key in data.keys():
        if isinstance(data[outer_key], dict):
            assert result[outer_key].keys() == data[outer_key].keys()
            for inner_key in data[outer_key].keys():
                assert result[outer_key][inner_key] \
                    == pytest.approx(data[outer_key][inner_key])
        else:
            assert result[outer_key] == data[outer_key]


def test_pack(serializer, data):

    buffer = serializer.packb('TestStruct', data)

    print('size', len(buffer))
    print(hexdump(buffer))

    res = flatbuffers_unpack(buffer)

    assert res.Foo() == data['foo']
    assert res.Bar() == data['bar']
    assert res.Value().A() == data['value']['a']
    assert res.Value().B() == pytest.approx(data['value']['b'])
    assert res.Value().E() == data['value']['e']


def test_defaults(serializer):

    struct = serializer.new('TestStructStruct')

    schema = serializer.registry.type_by_name('TestStructStruct')
    assert struct['a'] == schema['a'].default
    assert struct['b'] == schema['b'].default
    assert str(struct['e']).split('.')[-1] == schema['e'].default

    table = serializer.new('TestStruct', dict(value=struct))
    buffer = table.packb()

    print('size', len(buffer))
    print(hexdump(buffer))

    res = flatbuffers_unpack(buffer)

    assert res.Foo() == table['foo']
    assert res.Bar() == table['bar']
    assert res.Value().A() == table['value']['a']
    assert res.Value().B() == pytest.approx(table['value']['b'])
    assert res.Value().E() == table['value']['e']


def test_mutation(serializer, data):

    struct_a = serializer.new('TestStructStruct', {'a': 3, 'b': 4})
    struct_b = struct_a.evolve(b=5)

    assert struct_a['a'] == 3
    assert struct_a['b'] == 4

    assert struct_b['a'] == 3
    assert struct_b['b'] == 5


def test_bad_mutation(serializer):

    struct = serializer.new('TestStructStruct')

    with pytest.raises(ValueError):
        struct.evolve(a="hello")

    with pytest.raises(ValueError):
        struct.evolve(a=-1)


def test_init_from_dict(serializer):
    data = {
        'a': 1,
        'b': 2,
        'e': TestStructEnum.TestStructEnum.Bar
    }
    struct = serializer.new('TestStructStruct', data)
    assert dict(struct) == data


def test_init_from_tuple(serializer):
    data = (1, 2, TestStructEnum.TestStructEnum.Bar)
    struct = serializer.new('TestStructStruct', data)
    assert struct.astuple() == data


def test_init_from_bytes(serializer):
    data = (1, 2, TestStructEnum.TestStructEnum.Bar)
    bytes = serializer.new('TestStructStruct', data).asbytes()
    struct = serializer.new('TestStructStruct', bytes)
    assert struct.astuple() == data


def test_as_array(serializer, data):
    struct = serializer.new('TestStructStruct', data['value'])
    arr = struct.asarray()
    for key in struct.keys():
        assert arr[0][key] == struct[key]
    assert arr.tobytes() == struct.asbytes()
    print(hexdump(struct.asbytes()))


def test_as_tuple(serializer, data):
    struct = serializer.new('TestStructStruct', data['value'])
    tup = struct.astuple()
    for n, key in enumerate(struct.keys()):
        assert tup[n] == struct[key]


def test_cmp(serializer):
    data = (1, 2, TestStructEnum.TestStructEnum.Bar)
    struct_a = serializer.new('TestStructStruct', data)
    struct_b = serializer.new('TestStructStruct', data)
    struct_c = struct_b.evolve(b=4)

    assert struct_a == struct_b
    assert struct_a != struct_c
