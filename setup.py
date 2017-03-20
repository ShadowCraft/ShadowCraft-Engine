from distutils.core import setup

setup(
    name='ShadowCraft-Engine',
    url='http://github.com/ShadowCraft/ShadowCraft-Engine/',
    version='7.1.5',
    packages=[
        'shadowcraft',
        'shadowcraft.calcs',
        'shadowcraft.calcs.rogue',
        'shadowcraft.calcs.rogue.Aldriana',
        'shadowcraft.core',
        'shadowcraft.objects'
    ],
    license='LGPL',
    long_description=open('README.md').read(),
)
