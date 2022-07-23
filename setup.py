from distutils.core import setup

setup(
    name='rsmtpd',
    version='0.3.5',
    packages=['rsmtpd', 'rsmtpd.core', 'rsmtpd.handlers', 'rsmtpd.response'],
    url='',
    license='Apache 2.0',
    author='Al Trevino',
    author_email='alf@mypals.org',
    description='Research-Oriented SMTP Daemon',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    install_requires=['yaml'],
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
    entry_points={
        'console_scripts': [
            'rsmtpd=rsmtpd:main',
        ],
    }
)
