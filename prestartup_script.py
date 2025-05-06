import os
import subprocess
import sys

import folder_paths
from packaging.requirements import Requirement

base_path = folder_paths.base_path
requirements_file_path = os.path.join(base_path, "requirements.txt")


def parse_requirements(requirements):
    return {Requirement(line).name: Requirement(line) for line in requirements if line.strip()}


def install_package(package, upgrade=False):
    try:
        print(f"Installing package: {package}")
        if not upgrade:
            command = [sys.executable, "-m", "pip", "install", package]
        else:
            command = [sys.executable, "-m", "pip", "install", "--upgrade", package]
        subprocess.check_call(command)
    except subprocess.CalledProcessError as error:
        print(f"Failed to install package {package}: {error}")


def ensure_transformers():
    try:
        from transformers import CLIPTokenizer
    except ImportError as error:
        install_package("transformers", upgrade=True)
        restart()


def ensure_required_packages():
    required_packages = [
        "comfyui-frontend-package",
    ]

    with open(requirements_file_path, "r") as file:
        requirements = [line.strip() for line in file.readlines() if not line.startswith("#")]
        parsed_requirements = parse_requirements(requirements)

        for package_name in required_packages:
            if package_requirement := parsed_requirements.get(package_name):
                print(f"Package {package_requirement} found in requirements file")
                install_package(str(package_requirement))


def restart():
    sys_argv = sys.argv.copy()

    if sys_argv[0].endswith("__main__.py"):
        module_name = os.path.basename(os.path.dirname(sys_argv[0]))
        cmds = [sys.executable, "-m", module_name] + sys_argv[1:]

    elif sys.platform.startswith("win32"):
        cmds = ['"' + sys.executable + '"', '"' + sys_argv[0] + '"'] + sys_argv[1:]

    else:
        cmds = [sys.executable] + sys_argv

    os.execv(sys.executable, cmds)


def main():
    ensure_transformers()
    ensure_required_packages()


main()
