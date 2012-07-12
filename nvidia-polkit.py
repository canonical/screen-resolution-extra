#!/usr/bin/python
# -*- coding: utf-8 -*-
## Copyright (C) 2001-2008 Alberto Milone <albertomilone@alice.it>

## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


import sys, dbus, logging, os, re
import optparse

SERVICE_NAME   = 'com.ubuntu.ScreenResolution.Mechanism'
OBJECT_PATH    = '/'
INTERFACE_NAME = 'com.ubuntu.ScreenResolution.Mechanism'

# Usage:
# python /usr/share/screen-resolution-extra/nvidia-polkit.py --help
#

def get_xkit_service(widget=None):
    '''returns a dbus interface to the screenresolution mechanism'''
    service_object = dbus.SystemBus().get_object(SERVICE_NAME, OBJECT_PATH)
    service = dbus.Interface(service_object, INTERFACE_NAME)

    return service


def main(options):
    exit_code = 1
    
    conf = get_xkit_service()
    if not conf:
        # dbus_cant_connect
        logging.error("cannot connect to dbus service")
        sys.exit(1)
    
    if options.filename and options.backup_filename:
        logging.debug('making backup of /etc/X11/xorg.conf to %s and writing %s to /etc/X11/xorg.conf' \
        % (options.backup_filename, options.filename))
        exit_code = conf.backupAndWriteXorgConf([options.backup_filename, options.filename])
    elif options.filename and not options.backup_filename:
        logging.debug('writing %s to /etc/X11/xorg.conf' % options.filename)
        exit_code = conf.writeXorgConf(options.filename)
    elif not options.filename and options.backup_filename:
        logging.debug('making backup of /etc/X11/xorg.conf to %s' % options.backup_filename)
        exit_code = conf.backupXorgConf(options.backup_filename)
    elif not options.filename and not options.backup_filename:
        logging.error("called with wrong arguments")
        return exit_code

    # All went well if exit_code == 0
    return exit_code


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-w", "--write-from", dest="filename",
                      help="write xorg.conf from FILE", metavar="FILE")
    parser.add_option("-b", "--backup-to", dest="backup_filename",
                      help="backup file to FILE", metavar="FILE")

    (options, args) = parser.parse_args()
    
    operation_status = main(options)

    sys.exit(operation_status)


