#!/usr/bin/env python

import os, sys

if len(sys.argv) <= 1:
    os.system("xgettext -k_ -kN_ -o screen-resolution-extra.pot ../com.ubuntu.screen-resolution-extra.policy.in")
    print "Now edit messages.pot, save it as <locale>.po, and send it" \
        " to alberto.milone@canonical.com\nThanks!\n"
