import pytest

import flatboobs


@pytest.fixture(params=['fatboobs'])
def backend(request):
    return request.param


@pytest.fixture
def registry(backend):

    reg = flatboobs.Registry(backend=backend)
    reg.load_schema_from_package('fbtest.schema')

    return reg
