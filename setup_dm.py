from distutils.core import setup

setup(
    name='ShadowCraft-Engine',
    url='http://github.com/dazer/ShadowCraft-Engine/',
    version='0.1',
    packages=['shadowcraft',
        'shadowcraft.calcs', 'shadowcraft.calcs.rogue', 'shadowcraft.calcs.rogue.Aldriana',
        'shadowcraft.calcs.darkmantle', 'shadowcraft.calcs.darkmantle.rogue',
        'shadowcraft.core',
        'shadowcraft.objects'],
    license='LGPL',
    long_description=open('README').read(),
)
