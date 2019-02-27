# pylint: disable=missing-docstring
# TODO make separate package for buildcmake

import os
import subprocess
import sys
from distutils.cmd import Command  # type: ignore
from distutils.command.build import build as build_orig  # type: ignore

__version__ = '0.0.0'


def patch_sub_commands(sub_commands):

    patched = []

    for cmd, predecate in sub_commands:
        if cmd == 'build_ext':
            patched.append((cmd, lambda *args: True))
        else:
            patched.append((cmd, predecate))

    return patched


class Build(build_orig):

    # def run(self):
    #     self.run_command('build_cmake')
    #     super().run()

    sub_commands = patch_sub_commands(build_orig.sub_commands)


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

        self.set_undefined_options('build',
                                   ('build_temp', 'build_temp'),
                                   ('debug', 'debug'),
                                   ('parallel', 'parallel'),
                                   )

    def run(self):

        try:
            subprocess.check_output(['cmake', '--version'])
        except:
            raise RuntimeError(
                "CMake must be installed to build the following extensions: "
                + ", ".join(e.name for e in self.extensions)
            )

        self.get_finalized_command('build_py')

        src_dir = os.path.dirname(os.path.abspath(
            self.distribution.get_fullname()))
        build_dir = os.path.abspath(self.build_temp)
        build_py = self.get_finalized_command('build_py')
        install_dir = os.path.abspath(src_dir if self.inplace
                                      else build_py.build_lib)

        build_type = 'Debug' if self.debug else 'Release'
        cmake_args = []
        cmake_args += [f'-DPYTHON_EXECUTABLE={sys.executable}']
        cmake_args += [f'-DCMAKE_BUILD_TYPE={build_type}']
        cmake_args += [f'-DCMAKE_INSTALL_PREFIX={install_dir}']

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
            ['make'] + make_args + ['install'], cwd=build_dir)
