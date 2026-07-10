from setuptools import find_packages, setup

package_name = 'patrol_voice'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='wuge',
    maintainer_email='you@example.com',
    description='Voice announcement node for patrol events.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'voice_speaker = patrol_voice.voice_speaker:main',
            'patrol_voice = patrol_voice.voice_speaker:main',
        ],
    },
)
