from setuptools import find_packages, setup

metadata = {
    "version": "0.0.1",
    "name": "MDI TGS",
    "description": "Engine for telegram system",
    "authors": "MDI",
}

with open("requirements/prod.txt", encoding="utf-8") as fp:
    requirements = fp.read()

with open("requirements/test.txt", encoding="utf-8") as fp:
    test_requirements = fp.read()

setup(
    name=metadata["name"],
    version=metadata["version"],
    description=metadata["description"],
    author="MDI",
    author_email="moiseev.david@yandex.ru",
    packages=find_packages(),
    install_requires=requirements,
    zip_safe=False,
    keywords="mdi_tgs",
    test_suite="tests",
    tests_require=requirements + test_requirements,
)
