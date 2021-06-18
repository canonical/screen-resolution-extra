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
    author_email="alberto.milone@canonical.com",
    maintainer="Alberto Milone",
    maintainer_email="alberto.milone@canonical.com",
    url="http://www.albertomilone.com",
    license="gpl",
    description="Extension for the GNOME Screen Resolution applet",
    data_files=[
                ("share/polkit-1/actions", glob.glob("com.ubuntu.screen-resolution-extra.policy")),
                ("share/screen-resolution-extra", glob.glob("nvidia-polkit")),
               ],
    cmdclass = { "build" : build_extra.build_extra,
            "build_i18n" :  build_i18n.build_i18n,
            "build_help" :  build_help.build_help,
            "build_icons" :  build_icons.build_icons }
)





