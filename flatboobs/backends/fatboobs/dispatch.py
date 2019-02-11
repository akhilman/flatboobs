"""
Function dispatch declarations
"""

from multipledispatch import Dispatcher

# Callable[[
#   FatBoobs, Template, Optional[bytes], UOffset, Mapping[str, Any]
# ], Container]
new_container = Dispatcher(  # pylint: disable=invalid-name
    f'{__name__}.new_container'
)

# Callable[[FatBoobs, FieldTemplate, value], Any]
convert_field_value = Dispatcher(  # pylint: disable=invalid-name
    f"{__name__}.convert_field_value")


# Callable[[Table, FieldTemplate], Any]
read_field = Dispatcher(  # pylint: disable=invalid-name
    f"{__name__}.read_field")

# Callable[[Table, FieldTemplate], USize]
field_size = Dispatcher(  # pylint: disable=invalid-name
    f"{__name__}.field_size")

# Callable[[Table, FieldTemplate], str]
field_format = Dispatcher(  # pylint: disable=invalid-name
    f"{__name__}.field_format")


# Callable[[Container], Generator[Container, None, None]]
flatten = Dispatcher(f'{__name__}.flatten')  # pylint: disable=invalid-name

# Callable[[USize, Container], USize]
calc_size = Dispatcher(f'{__name__}.calc_size')  # pylint: disable=invalid-name

# Callable[[bytearray, UOffset, Mapping[int, UOffset], Container],
#          Tuple[UOffset, UOffset]]
write = Dispatcher(f'{__name__}.write')  # pylint: disable=invalid-name
