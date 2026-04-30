import setuptools
from setuptools import Extension

import os
from pathlib import Path

try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = None

os.environ["PYTHONIOENCODING"] = "utf-8"


def find_pyx_packages(base_dir):
    extensions = []
    for path in Path(base_dir).rglob("*.pyx"):
        module_name = ".".join(path.with_suffix("").parts)
        extensions.append(Extension(name=module_name, language="c++", sources=[str(path)]))
        print(f'add Extension: {module_name} {[str(path)]}')
    return extensions


def build_extensions(base_dir):
    extensions = find_pyx_packages(base_dir)
    if not extensions:
        return []
    if cythonize is None:
        raise RuntimeError("Cython is required to build .pyx extensions")
    return cythonize(extensions, compiler_directives={'language_level': "3"})


setuptools.setup(
    name="ok-ww",
    version="0.0.1",
    author="ok-oldking",
    author_email="firedcto@gmail.com",
    description="Automation with Computer Vision for Python",
    url="https://github.com/ok-oldking/ok-script",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'pywin32>=306; sys_platform == "win32"',
        'darkdetect>=0.8.0',
        'PySideSix-Frameless-Window>=0.4.3',
        'typing-extensions>=4.11.0',
        'PySide6-Essentials>=6.7.0',
        'GitPython>=3.1.43',
        'requests>=2.32.3',
        'psutil>=6.0.0'
    ],
    python_requires='>=3.9',
    ext_modules=build_extensions("src")
)
