#!/usr/bin/python

from distutils.core import setup

import subprocess, glob, os.path

from DistUtilsExtra.command import *

#mo_files = []
## HACK: make sure that the mo files are generated and up-to-date
#subprocess.call(["make", "-C", "po", "build-mo"])
#for filepath in glob.glob("po/mo/*/LC_MESSAGES/*.mo"):
#    lang = filepath[len("po/mo/"):]
#    targetpath = os.path.dirname(os.path.join("share/locale",lang))
#    mo_files.append((targetpath, [filepath]))

setup(
    name="screen-resolution-extra",
    author="Alberto Milone",
    author_email="albertomilone@alice.it",
    maintainer="Alberto Milone",
    maintainer_email="albertomilone@alice.it",
    url="http://www.albertomilone.com",
    license="gpl",
    description="Extension for the GNOME Screen Resolution applet",
    packages=["ScreenResolution"],
    data_files=[
                ("/etc/dbus-1/system.d", glob.glob("com.ubuntu.ScreenResolution.Mechanism.conf")),
                ("share/dbus-1/system-services", glob.glob("com.ubuntu.ScreenResolution.Mechanism.service")),
                ("share/polkit-1/actions", glob.glob("screenresolution-mechanism.policy")),
                ("share/screen-resolution-extra", glob.glob("screenresolution-mechanism.py")),
                ("share/screen-resolution-extra", glob.glob("policyui.py")),
                ("share/screen-resolution-extra", glob.glob("nvidia-polkit.py")),
                ("share/screen-resolution-extra", glob.glob("nvidia-prime.py")),
               ],
    cmdclass = { "build" : build_extra.build_extra,
            "build_i18n" :  build_i18n.build_i18n,
            "build_help" :  build_help.build_help,
            "build_icons" :  build_icons.build_icons }
)





