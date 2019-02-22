"""
TODO Write module docstring
"""
# pylint: disable=missing-docstring

from pathlib import Path
from typing import Callable, Optional, Sequence

import click
import toolz.functoolz as ft

import flatboobs.codegen
from flatboobs import logging


@click.group()
@click.option('--debug/-no-debug', default=False)
@click.pass_context
def main(
        ctx: click.Context,
        debug: bool = False,
) -> None:
    logging.setup_logging(debug)
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug


def common_options(func: Callable) -> Callable:
    return ft.compose(
        click.option(
            '--output-dir', '-o', default='./',
            type=click.Path(
                file_okay=False, dir_okay=True, writable=True,
                resolve_path=True)),
        click.option(
            '--include-path', '-I', multiple=True,
            type=click.Path(
                file_okay=False, dir_okay=True, readable=True,
                resolve_path=True)),
        click.option('--header-only/--no-header-only', default=False,
                     help="Generated header only library"),
        click.option('--no-rpc', 'rpc', flag_value=None, default=True),
        click.option('--grpclib', 'rpc', flag_value='grpclib'),
        click.option('--python/--no-python', default=False,
                     help="Generate python module"),
    )(func)


@main.command(help="Generates CMakeLists.txt file.")
@common_options
@click.option('--project-name', '-p', default=None)
@click.argument(
    'schema_path', nargs=-1,
    type=click.Path(
        file_okay=False, dir_okay=True, readable=True, resolve_path=True))
def cmake(
        # pylint: disable=too-many-arguments
        project_name: Optional[str] = None,
        output_dir: str = './',
        include_path: Sequence[str] = tuple(),
        header_only: bool = False,
        rpc: Optional[str] = None,
        python: bool = False,
        schema_path: Sequence[str] = tuple()
):
    if not project_name:
        project_name = Path(output_dir).stem
    flatboobs.codegen.cmakelists.generate(
        project_name,
        list(map(Path, schema_path)) if schema_path else [
            Path.cwd().resolve()],
        list(map(Path, include_path)),
        Path(output_dir),
        rpc=rpc,
        python=python,
    )


@main.command(help="Generates [de]serializer code.")
@common_options
@click.argument(
    'schema_file', nargs=-1,
    type=click.Path(
        file_okay=True, dir_okay=False, readable=True, resolve_path=True))
def lazy(
        # pylint: disable=too-many-arguments
        output_dir: str = './',
        include_path: Sequence[str] = tuple(),
        header_only: bool = False,
        schema_file: Sequence[str] = tuple(),
        rpc: Optional[str] = None,
        python: bool = False,
):
    flatboobs.codegen.sources.generate(
        list(map(Path, schema_file)),
        list(map(Path, include_path)),
        Path(output_dir),
        options={
            "header_only": header_only,
            "rpc": rpc,
            "python": python,
        }
    )


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    # pylint: disable=unexpected-keyword-arg
    main(obj=dict())
