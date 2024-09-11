from setuptools import setup, find_packages


__version__ = "2.0.14"


setup(
    # package name in pypi
    name="django-oscar-elasticsearch",
    # extract version from module.
    version=__version__,
    description="Search app for oscar using elasticsearch",
    long_description="Search app for oscar using elasticsearch",
    classifiers=[],
    keywords="",
    author="Lars van de Kerkhof",
    author_email="specialunderwear@gmail.com",
    url="https://github.com/specialunderwear/django-oscar-elasticsearch",
    license="GPL",
    # include all packages in the egg, except the test package.
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    namespace_packages=[],
    # include non python files
    include_package_data=True,
    zip_safe=False,
    # specify dependencies
    install_requires=[
        "django>=1.11",
        "setuptools",
        "django-oscar>=1.6",
        "wagtail>=2,<3",
        "purl",
        "elasticsearch>=6.0.0,<7.0.0",
        "uwsgidecorators-fallback",
        "wagtail-extendedsearch",
    ],
    # mark test target to require extras.
    extras_require={
        "test": [
            "mock",
            "coverage>=5.4,<5.5",
            "sorl-thumbnail>=12.9,<12.10",
            "django-oscar @ git+https://github.com/django-oscar/django-oscar.git",
        ],
        "dev": ["pylint>=2.17.4", "pylint-django>=2.5.3", "black>=23.3.0"],
    },
)
