# pylint: disable=missing-docstring

from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from jinja2 import Environment, PackageLoader, Template
from toolz import functoolz as ft

from flatboobs import idl  # type: ignore
from flatboobs import logging

from .cpp_format import cpp_format
from .utils.filters import filters
from .utils.tests import tests

logger = logging.getLogger()


def make_renderer(
        parser: idl.Parser,
        options: Mapping[str, Any],
        output_dir: Path,
) -> Callable[[Template, str, Callable[[str], str]], None]:

    def render(
            template: Template,
            output_suffix: str,
            postprocessor: Callable[[str], str] = ft.identity
    ) -> None:
        root_struct_def = parser.root_struct_def
        root_fname = Path(root_struct_def.file)
        output_file = output_dir / f'{root_fname.stem}{output_suffix}'

        logger.info("Rendering %s", output_file)
        with output_file.open('w') as output:
            output.write(
                postprocessor(
                    template.render(
                        parser=parser,
                        output_file=output.name,
                        options=options,
                    )
                )
            )

    return render


def generate_one(
        env: Environment,
        parser: idl.Parser,
        options: Mapping[str, Any],
        output_dir: Path
):
    render = make_renderer(parser, options, output_dir)
    render(env.get_template("cpp/main.hpp.txt"), "_flatboobs.hpp", cpp_format)
    if not options.get("header_only", False):
        render(env.get_template("cpp/main.cpp.txt"),
               "_flatboobs.cpp", cpp_format)


def generate(
        # pylint: disable
        schema_files: Sequence[Path],
        include_paths: Sequence[Path],
        output_dir: Path,
        options: Mapping[str, Any],
) -> None:

    env = Environment(
        loader=PackageLoader('flatboobs', 'templates'),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters.update(filters(output_dir, options))
    env.tests.update(tests(output_dir, options))
    env.globals = {
        'BaseType': idl.BaseType,
    }

    pending = set(schema_files)
    done = set()
    while pending:
        fname = pending.pop()
        logger.info("Loading schema %s", fname)
        parser = idl.parse_file(str(fname), list(map(str, include_paths)))
        root_struct_def = parser.root_struct_def

        generate_one(env, parser, options, output_dir)

        done.add(Path(root_struct_def.file))
        for inc in map(Path, parser.included_files):
            if inc in done:
                continue
            pending.add(inc)
