from distutils.core import setup
setup(
    name = "checkrainpi",
    packages = ["raingauge"],
    version = "1.0.0",
    description = "Rainwater gauge collector",
    author = "Rodney Lorrimar",
    author_email = "dev@rodney.id.au",
    url = "https://github.com/rvl/checkrainpi",
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        ],
    long_description = """
Collect measurements over the serial port, store them, send them.
""",
    entry_points = { "console_scripts": [
        "checkrain = raingauge.check:main",
        "getrain = raingauge.retrieve:main",
    ] },
)
