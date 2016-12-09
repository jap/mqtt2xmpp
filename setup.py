from distutils.core import setup

version = '0.1'

setup(name='mqtt2xmpp',
      version=version,
      packages=['mqtt2xmpp'],
      install_requires=[
          'dnspython',
          'paho-mqtt>=1.1,<1.2',
          'PyYAML>=3.11,<3.12',
          'sleekxmpp>=1.3.1,<=1.3.2',
      ],
      entry_points = {
          'console_scripts': ['mqtt2xmpp=mqtt2xmpp.main:main']
      }
     )
