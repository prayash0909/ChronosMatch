
from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        name="matching_engine.engine",
        sources=["matching_engine/engine.pyx"],
    )
]

setup(
    name="ChronosMatch",
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3"},
    ),
)
