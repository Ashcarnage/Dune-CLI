from setuptools import setup, find_packages

setup(
    name='dune-cli',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # List your project dependencies here.
        'google-auth',
        'google-auth-oauthlib',
        'requests',
        'rich',
        'groq',
        'textual',
        # 'googlesearch-python>=1.0.0',
        # 'rich-gradient',
        # 'cheap_repr',
        # 'snoop',
    ],
    entry_points={
        'console_scripts': [
            'dune=dune.rich_ui:main',
        ],
    },
    author='Your Name',
    author_email='your.email@example.com',
    description='A Gemini-powered CLI assistant.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/dune-cli', # Replace with your project's URL
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
) 