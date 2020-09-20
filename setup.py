import setuptools

setuptools.setup(
    name="dso-tools",
    use_scm_version=True,
    author="Rafał Florczak",
    author_email="florczak.raf+dsotools@gmail.com",
    description="A set of tools for analysing and modifying Torque3d VM bytecode",
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    setup_requires=["setuptools_scm"],
    extras_require={
        "dev": ["pytest", "black"],
    },
)
