#!/usr/bin/python
# -*- coding: utf-8 -*-
## Copyright 2013 Canonical Ltd.
##
## Author: Alberto Milone <alberto.milone@canonical.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


import sys, dbus, logging

SERVICE_NAME   = 'com.ubuntu.ScreenResolution.Mechanism'
OBJECT_PATH    = '/'
INTERFACE_NAME = 'com.ubuntu.ScreenResolution.Mechanism'

# Usage:
# python /usr/share/screen-resolution-extra/nvidia-prime.py --help
#

def get_prime_service(widget=None):
    '''returns a dbus interface to the screenresolution mechanism'''
    service_object = dbus.SystemBus().get_object(SERVICE_NAME, OBJECT_PATH)
    service = dbus.Interface(service_object, INTERFACE_NAME)

    return service


def usage():
    sys.stderr.write("Usage: %s nvidia|intel\n" % (sys.argv[0]))


if __name__ == '__main__':
    try:
        arg = sys.argv[1]
    except IndexError:
        arg = None

    if len(sys.argv[1:]) != 1:
        usage()
        exit(1)

    if arg == 'intel' or arg == 'nvidia':
        conf = get_prime_service()
        if not conf:
            # dbus_cant_connect
            logging.error("cannot connect to dbus service")
            sys.exit(1)

        # Exit using the retcode
        try:
            sys.exit(conf.prime_select(arg))
        except dbus.exceptions.DBusException as e:
            message = '%s' % e
            sys.stderr.write(message)
            if 'AccessDeniedException' in message:
                # The user probably did not enter the password
                # or cancelled
                sys.exit(5)
            else:
                sys.exit(1)
    else:
        usage()
        sys.exit(1)
