# pylint: disable=missing-docstring

from pathlib import Path
from typing import Any, Mapping, Sequence

from jinja2 import Environment, PackageLoader

from flatboobs import idl  # type: ignore
from flatboobs import load_schema, logging

from .clang_format import clang_format
from .filters import FILTERS
from .tests import TESTS

logger = logging.getLogger()


def make_code(
        env: Environment,
        template: str,
        output_file: Path,
        options: Mapping[str, Any],
):
    output_file = output_file.resolve()

    logger.info("Rendering %s", output_file)
    options = dict(options)
    options.update({
        'output_file': output_file,
    })

    txt = env.get_template(template).render(**options)
    if options.get('clang_format', True):
        txt = clang_format(txt)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(txt, encoding='utf-8')


def generate_cpp(
        schema_files: Sequence[Path],
        include_paths: Sequence[Path],
        output_dir: Path,
        library_name: str,
        options: Mapping[str, Any],
) -> None:

    env = Environment(
        loader=PackageLoader('flatboobs', 'templates'),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters.update(FILTERS)
    env.tests.update(TESTS)
    env.globals.update({
        'BaseType': idl.BaseType,
    })

    options = dict(options)
    options['library_name'] = library_name

    for schema_file, parser in load_schema(schema_files, include_paths):

        options['parser'] = parser
        options['schema_file'] = schema_file

        template = "cpp/main.hpp.txt"
        output_file = (output_dir / 'include' / library_name
                       / f"{schema_file.stem}.hpp")
        make_code(env, template, output_file, options)

        if not options.get("header_only", False):

            template = "cpp/main.cpp.txt"
            output_file = (output_dir / 'src' / library_name
                           / f"{schema_file.stem}.cpp")
            make_code(env, template, output_file, options)
