import enum

import flatbuffers
import pytest

from fbtest.schema import TestEnum, TestEnumEnum, TestEnumFlag
from flatboobs.utils import hexdump


@pytest.fixture
def data():
    return {
        "test_flag": (TestEnumFlag.TestEnumFlag.Foo
                      | TestEnumFlag.TestEnumFlag.Buz),
        "test_enum": TestEnumEnum.TestEnumEnum.Bar,
    }


def flatbuffers_pack(data):

    builder = flatbuffers.Builder(1024)

    TestEnum.TestEnumStart(builder)
    TestEnum.TestEnumAddTestEnum(builder, data['test_enum'])
    TestEnum.TestEnumAddTestFlag(builder, data['test_flag'])
    root = TestEnum.TestEnumEnd(builder)

    builder.Finish(root)

    return builder.Output()


def flatbuffers_unpack(buffer):
    return TestEnum.TestEnum.GetRootAsTestEnum(buffer, 0)


def test_unpack(registry, data):

    buffer = flatbuffers_pack(data)

    print('size', len(buffer))
    print(hexdump(buffer))

    table = registry.unpackb(buffer, root_type='TestEnum')

    from pprint import pprint
    pprint(table)
    assert len(table) == len(data)
    assert frozenset(table) == frozenset(data)
    assert frozenset(table.keys()) == frozenset(data.keys())

    for key in data.keys():
        print(key, table[key])
        assert table[key] == data[key]


def test_pack(registry, data):

    table = registry.new(type_name='TestEnum')
    table = table.evolve(**data)

    buffer = table.packb()

    print('size', len(buffer))
    print(hexdump(buffer))

    res = flatbuffers_unpack(buffer)

    assert res.TestEnum() == data['test_enum']
    assert res.TestFlag() == data['test_flag']


@pytest.mark.parametrize('key,enum_class, flatbuffers_enum', [
    ('test_enum', enum.IntEnum, TestEnumEnum.TestEnumEnum),
    ('test_flag', enum.IntFlag, TestEnumFlag.TestEnumFlag)
])
def test_enum(registry, key, enum_class, flatbuffers_enum):

    table = registry.new(type_name='TestEnum')
    enum_class = type(table[key])

    assert isinstance(table[key], enum_class)
    for name in ['Foo', 'Bar', 'Buz']:
        assert name in enum_class.__members__
        assert getattr(enum_class, name) == getattr(flatbuffers_enum, name)


def test_convert(registry):

    table = registry.new(type_name='TestEnum')
    enum_class = type(table['test_enum'])

    table = table.evolve(test_enum='Bar')
    assert isinstance(table['test_enum'], enum_class)
    assert table['test_enum'] == enum_class.Bar
