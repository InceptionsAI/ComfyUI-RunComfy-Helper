import os
import subprocess
import sys

import folder_paths
from packaging.requirements import Requirement

base_path = folder_paths.base_path
requirements_file_path = os.path.join(base_path, "requirements.txt")


def parse_requirements(requirements):
    return {Requirement(line).name: Requirement(line) for line in requirements if line.strip()}


def install_package(package):
    try:
        print(f"Installing package: {package}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError as error:
        print(f"Failed to install package {package}: {error}")


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


def main():
    ensure_required_packages()


main()
