from setuptools import setup, find_packages

setup(
    name="retirement-planner",
    version="1.0.0",
    description="Retirement planning web app with tax modeling",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.39.0",
        "pandas>=2.2.0",
        "altair>=5.2.0",
    ],
)

