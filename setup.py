from setuptools import setup, find_packages


__version__ = "1.0.1"


setup(
    # package name in pypi
    name="django-oscar-elasticsearch",
    # extract version from module.
    version=__version__,
    description="Search app for oscar using elasticsearch",
    long_description="Blablabla ... nothing ... Search app for oscar using elasticsearch",
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
        "setuptools",
        "django-oscar<2.0",
        "wagtail",
        "purl",
        "elasticsearch>=6.0.0,<7.0.0",
        "uwsgidecorators-fallback",
        "wagtail-extendedsearch",
    ],
    # mark test target to require extras.
    extras_require={"test": ["mock"]},
)
