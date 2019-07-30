import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="search",
    version="0.0.1",
    author="Brian Alexander",
    author_email="brian@dadgumsalsa.com",
    description="An app to search for resources.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/balexander85/search",
    packages=setuptools.find_packages(),
    install_requires=["requests", "requests-html", "humanfriendly", "retrying"],
    include_package_data=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
