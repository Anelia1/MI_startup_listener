'''
Author: Giancarlo Grasso
Contributor: Anelia Gaydardzhieva
Comments:
This file is an adapted copy of the build.py 
written by Giancarlo Grasso who solved major nuitka 
compilation challenges for UCL MotionInput project.
'''
import argparse
import subprocess
import sys

nuitka_args = [
    '--standalone',
    '--assume-yes-for-downloads',
    '--include-data-dir=data=data',
    '--include-data-dir=assets=assets',
    '--windows-icon-from-ico=ucl_logo.ico',
    '--include-data-files=info=info',
    '--output-dir=Release',
    '--nofollow-import-to=PySide6',
    '--plugin-enable=pyside6'
]


def build():
    parser = argparse.ArgumentParser(description='Build motion input with Nuitka.')
    parser.add_argument('--lto', action='store_true',
                        help='Use link time optimisation. Default: False')
    parser.add_argument('--console', action='store_true',
                        help='Show console when running the built executable. Default: False')
    parser.add_argument('target_file', type=str,
                        help='Target file to build.')
    
    args = parser.parse_args()
    print(args)
    if sys.platform == "darwin": nuitka_args.append('--macos-create-app-bundle') # MacOS
    if args.lto: nuitka_args.append('--lto=yes')
    else: nuitka_args.append('--lto=no')
    if not args.console: nuitka_args.append('--windows-disable-console')



    subprocess.call([sys.executable, "-m", "nuitka"] + nuitka_args + [args.target_file])

if __name__ == "__main__":
    build()
    