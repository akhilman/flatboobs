from flatc import flatc_packb, flatc_unpackb

SCHEMA = """
namespace flatboobs.test;

table Content {
    number:int;
    real:double = 10e1;
    default:byte = 7;
}

root_type Content;
file_identifier "TEST";
"""

def test_pack_unpack(tmp_path):

    ref = {
        'number': 123,
        'real': 321.123,
        'default': 7,
    }

    buffer = flatc_packb(SCHEMA, ref, tmp_path)
    res = flatc_unpackb(SCHEMA, buffer, tmp_path)

    assert ref == res
