# pylint: disable=missing-docstring
# TODO make separate package for buildcmake

import os
import subprocess
import sys
from distutils.cmd import Command  # type: ignore
from pathlib import Path

__version__ = '0.0.0'


class CMakeExtension:
    # pylint: disable=too-few-public-methods

    def __init__(self, package,
                 target='install', directory='./', cmake_args=tuple()):

        self.package = package
        self.target = target
        self.directory = directory
        self.cmake_args = cmake_args

    @property
    def name(self):
        return self.package


class BuildCmake(Command):

    description = 'run CMake'

    user_options = [
        ('debug', 'g',
         "compile/link with debugging information"),
        ('inplace', 'i',
         "ignore build-lib and put compiled extensions into the source " +
         "directory alongside your pure Python modules"),
        ('parallel=', 'j',
         "number of parallel build jobs"),
    ]
    boolean_options = ['debug', 'inplace']

    def initialize_options(self):
        # pylint: disable=attribute-defined-outside-init

        self.build_temp = None
        self.debug = False
        self.inplace = False
        self.parallel = False

    def finalize_options(self):
        # pylint: disable=attribute-defined-outside-init

        self.set_undefined_options('build',
                                   ('build_temp', 'build_temp'),
                                   ('debug', 'debug'),
                                   ('parallel', 'parallel'),
                                   )

    def run(self):

        try:
            subprocess.check_output(['cmake', '--version'])
        except subprocess.CalledProcessError:
            raise RuntimeError(
                "CMake must be installed to build the following extensions: "
                + ", ".join(e.name for e in self.extensions)
            )

        for ext in self.distribution.ext_modules:
            assert isinstance(ext, CMakeExtension)
            self.build(ext)

    def build(self, ext):

        build_py = self.get_finalized_command('build_py')

        distribution_dir = Path(
            self.distribution.get_fullname()).resolve().parent
        src_dir = distribution_dir / ext.directory
        src_dir = src_dir.resolve()
        build_dir = Path(self.build_temp).resolve()

        if self.inplace:
            install_dir = distribution_dir
        else:
            install_dir = Path(build_py.build_lib)
        for pack in ext.package.split('.'):
            install_dir /= pack
        install_dir = install_dir.resolve()

        build_type = 'Debug' if self.debug else 'Release'
        cmake_args = []
        cmake_args += [f'-DPYTHON_EXECUTABLE={sys.executable}']
        cmake_args += [f'-DCMAKE_BUILD_TYPE={build_type}']
        cmake_args += [f'-DCMAKE_INSTALL_PREFIX={install_dir}']
        cmake_args.extend(ext.cmake_args)

        make_args = []
        if self.parallel:
            make_args += [f'-j{self.parallel}']

        env = os.environ.copy()

        os.makedirs(build_dir, exist_ok=True)
        os.makedirs(install_dir, exist_ok=True)

        subprocess.check_call(['cmake', src_dir] +
                              cmake_args, cwd=build_dir, env=env)
        subprocess.check_call(['make'] + make_args, cwd=build_dir)
        subprocess.check_call(
            ['make'] + make_args + [ext.target], cwd=build_dir)

    @staticmethod
    def get_source_files():
        return []
