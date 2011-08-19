#!/usr/bin/env python

import os, sys

if len(sys.argv) <= 1:
    os.system("xgettext -k_ -kN_ -o screen-resolution-extra.pot ../ScreenResolution/ui.py")
    print "Now edit messages.pot, save it as <locale>.po, and send it" \
        " to albertomilone@alice.it.\nThanks!\n"
