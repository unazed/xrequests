import setuptools

with open("requirements.txt") as fp:
    requirements = fp.read().splitlines()

setuptools.setup(
    name="xrequests",
    author="h0nda",
    author_email="1@1.com",
    description="A faster alternate for the requests library",
    url="https://github.com/h0nde/xrequests",
    packages=setuptools.find_packages(),
    classifiers=[],
    install_requires=requirements
)
