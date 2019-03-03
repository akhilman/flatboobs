"""
TODO Write module docstring
"""
# pylint: disable=missing-docstring

from pathlib import Path
from typing import Optional, Sequence

import click

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


@main.command(help="Generates CMakeLists.txt file.")
@click.option('--project-name', '-p', default=None)
@click.option(
    '--output-dir', '-o', default='./',
    type=click.Path(
        file_okay=False, dir_okay=True, writable=True, resolve_path=True))
@click.option(
    '--include-path', '-I', multiple=True,
    type=click.Path(
        file_okay=False, dir_okay=True, readable=True, resolve_path=True))
@click.option('--no-grpc', 'grpc', flag_value=None, default=True)
@click.option('--grpclib', 'grpc', flag_value='grpclib')
@click.argument(
    'schema_path', nargs=-1,
    type=click.Path(
        file_okay=False, dir_okay=True, readable=True, resolve_path=True))
def cmake(
        project_name: Optional[str] = None,
        output_dir: str = './',
        include_path: Sequence[str] = tuple(),
        grpc: Optional[str] = None,
        schema_path: Sequence[str] = tuple()
):
    if not project_name:
        project_name = Path(output_dir).stem
    flatboobs.codegen.cmakelists.generate(
        project_name,
        list(map(Path, schema_path)) if schema_path else [
            Path.cwd().resolve()],
        list(map(Path, include_path)),
        grpc,
        Path(output_dir)
    )


@main.command(help="Generates [de]serializer code.")
@click.option(
    '--output-dir', '-o', default='./',
    type=click.Path(
        file_okay=False, dir_okay=True, writable=True, resolve_path=True))
@click.option(
    '--include-path', '-I', multiple=True,
    type=click.Path(
        file_okay=False, dir_okay=True, readable=True, resolve_path=True))
@click.argument(
    'schema_file', nargs=-1,
    type=click.Path(
        file_okay=True, dir_okay=False, readable=True, resolve_path=True))
def serializer(
        output_dir: str = './',
        include_path: Sequence[str] = tuple(),
        schema_file: Sequence[str] = tuple()
):
    flatboobs.codegen.serializer.generate(
        list(map(Path, schema_file)),
        list(map(Path, include_path)),
        Path(output_dir)
    )


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    # pylint: disable=unexpected-keyword-arg
    main(obj=dict())
