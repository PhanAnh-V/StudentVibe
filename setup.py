from setuptools import setup, find_packages

setup(
    name="vibecheck",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "gunicorn",
        "firebase-admin",
        "flask-wtf",
        "wtforms",
        "openai",
        "python-dotenv"
    ],
)
