import setuptools

with open("README.md") as fh:
    long_description = fh.read()

setuptools.setup(
        name = "csvsql",
        version = "1.0.0",
        author = "Moisès Gómez Girón",
        author_email = "moiatgit@gmail.com",
        description = "API to allow execution of SQL statements on csv files",
        long_description = long_description,
        long_description_content_type = "text/markdown",
        url = "https://github.com/moiatgit/csvsql",
        packages = setuptools.find_packages(),
        classifiers = (
            "Programming Language :: Python :: 3.5",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: POSIX :: Linux",
            "Natural Language :: English",
            "Topic :: Utilities",
            ),
        )
