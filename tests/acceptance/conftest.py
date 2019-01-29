import pytest

import flatboobs


@pytest.fixture(params=['fatboobs'])
def backend(request):
    return request.param


@pytest.fixture
def registry(backend, schema_str):

    reg = flatboobs.Registry(backend=backend)
    reg.load_schema_from_string(schema_str)

    return reg

