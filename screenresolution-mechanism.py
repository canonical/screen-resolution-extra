#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Fluendo Embedded S.L. (www.fluendo.com)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# taken from:
# https://code.fluendo.com/remotecontrol/trac/browser/trunk/
#         gnome_lirc_properties/backend.py?rev=217
# 
# modified by Harald Hoyer <harald@redhat.com>
#
# modified by Alberto Milone (tseliot) <albertomilone@alice.it>

import dbus, dbus.service, gobject, logging
import os, os.path
import sys
from xkit import xutils, xorgparser
import time
import shutil
import subprocess

# Modern flavors of dbus bindings have that symbol in dbus.lowlevel,
# for old flavours the internal _dbus_bindings module must be used.

try:
    # pylint: disable-msg=E0611
    from dbus.lowlevel import HANDLER_RESULT_NOT_YET_HANDLED

except ImportError:
    from _dbus_bindings import HANDLER_RESULT_NOT_YET_HANDLED

class AccessDeniedException(dbus.DBusException):
    '''This exception is raised when some operation is not permitted.'''

    _dbus_error_name = 'com.ubuntu.screenresolution.Mechanism.AccessDeniedException'

class UnsupportedException(dbus.DBusException):
    '''This exception is raised when some operation is not supported.'''

    _dbus_error_name = 'com.ubuntu.screenresolution.Mechanism.UnsupportedException'

class UsageError(dbus.DBusException):
    '''This exception is raised when some operation was not used properly.'''

    _dbus_error_name = 'com.ubuntu.screenresolution.Mechanism.UsageError'

class PolicyKitService(dbus.service.Object):
    '''A D-BUS service that uses PolicyKit for authorization.'''

    def _check_permission(self, sender, conn, action, reconnect=True):
        '''
        Verifies if the specified action is permitted, and raises
        an AccessDeniedException if not.
        '''
        if sender is None and conn is None:
            # called locally, not through D-BUS
            return

        # get peer PID
        dbus_info = dbus.Interface(conn.get_object('org.freedesktop.DBus',
              '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        pid = dbus_info.GetConnectionUnixProcessID(sender)

        # query PolicyKit
        polkit = dbus.Interface(get_service_bus().get_object(
                'org.freedesktop.PolicyKit1',
                '/org/freedesktop/PolicyKit1/Authority', False),
                'org.freedesktop.PolicyKit1.Authority')
        try:
            # we don't need is_challenge return here, since we call with AllowUserInteraction
            (is_auth, _, details) = polkit.CheckAuthorization(
                    ('unix-process', {'pid': dbus.UInt32(pid, variant_level=1),
                     'start-time': dbus.UInt64(0, variant_level=1)}),
                    action, {'': ''}, dbus.UInt32(1), '', timeout=600)
        except dbus.DBusException, e:
            if reconnect and e._dbus_error_name == 'org.freedesktop.DBus.Error.ServiceUnknown':
                # polkitd timed out, connect again
                return self._check_polkit_privilege(sender, conn, action, reconnect=False)
            else:
                raise

        if not is_auth:
            logging.debug('_check_permission: sender %s on connection %s pid %i is not authorized for %s: %s' %
                    (sender, conn, pid, action, str(details)))
            raise AccessDeniedException(action)


class BackendService(PolicyKitService):
    '''A D-Bus service that PolicyKit controls access to.'''

    # pylint: disable-msg=C0103,E0602

    INTERFACE_NAME = 'com.ubuntu.ScreenResolution.Mechanism'
    SERVICE_NAME   = 'com.ubuntu.ScreenResolution.Mechanism'
    IDLE_TIMEOUT   =  30

    def __init__(self, connection=None, path='/'):        
        if connection is None:
            connection = get_service_bus()

        super(BackendService, self).__init__(connection, path)

        self.__name = dbus.service.BusName(self.SERVICE_NAME, connection)
        self.__loop = gobject.MainLoop()
        self.__timeout = 0
        connection.add_message_filter(self.__message_filter)

    def __message_filter(self, connection, message):
        '''
        D-BUS message filter that keeps the service alive,
        as long as it receives message.
        '''

        if self.__timeout:
            self.__start_idle_timeout()

        return HANDLER_RESULT_NOT_YET_HANDLED

    def __start_idle_timeout(self):
        '''Restarts the timeout for terminating the service when idle.'''

        if self.__timeout:
            gobject.source_remove(self.__timeout)

        self.__timeout = gobject.timeout_add(self.IDLE_TIMEOUT * 1000,
                                             self.__timeout_cb)

    def __timeout_cb(self):
        '''Timeout callback that terminates the service when idle.'''

        # Keep service alive, as long as additional objects are exported:
        if self.connection.list_exported_child_objects('/'):
            return True

        print 'Terminating %s due to inactivity.' % self.SERVICE_NAME
        self.__loop.quit()

        return False

    def run(self):
        '''Creates a GLib main loop for keeping the service alive.'''

        print 'Running %s.' % self.SERVICE_NAME
        print ('Terminating it after %d seconds of inactivity.' 
               % self.IDLE_TIMEOUT)

        self.__start_idle_timeout()
        self.__loop.run()


    # pylint: disable-msg=R0913
    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='as', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')   
    def setVirtual(self, virtres, sender=None, conn=None):
        '''
        Replace the first line of this example with a source and a destination file
        '''
        self._check_permission(sender, conn,
            'com.ubuntu.screenresolution.mechanism.configure')

        virtual = ' '.join(virtres)
        
        source = '/etc/X11/xorg.conf'
        destination = '/etc/X11/xorg.conf'
        
        if os.path.exists(source):
            #make a backup of the xorg.conf
            backup = source + "." + time.strftime("%Y%m%d%H%M%S")
            shutil.copyfile(source, backup)
        
        try:
            a = xutils.XUtils(source)
        except(IOError, xorgparser.ParseException):#if xorg.conf is missing or broken
            a = xutils.XUtils()#start from scratch
        
        empty = True
        for section in a.globaldict:
            if len(a.globaldict[section]) > 0:
                empty = False
                break

        if empty:
            a.make_section('Device', 'Configured Video Device')
            a.make_section('Screen', identifier='Configured Screen Device')
            a.add_reference('Screen', 'Device', 'Configured Video Device', position=0)
            a.make_subsection('Screen', 'Display', position=0)
            a.add_suboption('Screen', 'Display', 'Virtual', value=virtual, position=0)
        
        else:#if xorg.conf exists and is not empty
            devicelen = len(a.globaldict['Device'])
            screenlen = len(a.globaldict['Screen'])
            
            if screenlen == 0:
                screen = a.make_section('Screen', identifier='Configured Screen Device')
                if devicelen == 0:
                    device = a.make_section('Device', 'Configured Video Device')
                else:
                    device = 0
                a.add_reference('Screen', 'Device', 'Configured Video Device', position=device)
                
                a.make_subsection('Screen', 'Display', position=0)
                a.add_suboption('Screen', 'Display', 'Virtual', value=virtual, position=0)
                
            else:#if at least 1 Screen section exists
                '''
                Set the virtual section in all the Screen sections
                '''
                for screen in a.globaldict['Screen']:
                    a.make_subsection('Screen', 'Display', position=screen)
                    a.add_suboption('Screen', 'Display', 'Virtual', value=virtual, position=screen)

        '''
        Write the changes to the destination file
        '''
        a.write(destination)
        return True
    
    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='s', out_signature='i',
                         sender_keyword='sender', connection_keyword='conn')
    def setDontZap(self, enable, sender=None, conn=None):
        '''Try to set the DontZap option in the xorg.conf
           and return the exit code of dontzap'''

        self._check_permission(sender, conn,
            'com.ubuntu.screenresolution.mechanism.dontzap')

        dontzap_file = '/usr/bin/dontzap'
        if not os.path.isfile(dontzap_file):
            logging.error('/usr/bin/dontzap does not exist')
            return 1
        
        if enable in ['--enable', '--disable']:
            logging.debug('calling dontzap with %s' % enable)
            retcode = subprocess.call([dontzap_file, enable])
            return retcode
        else:
            logging.error('called with wrong arguments = %s' % enable)
            return 1

    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='s', out_signature='i',
                         sender_keyword='sender', connection_keyword='conn')
    def backupXorgConf(self, backup_file, sender=None, conn=None):
        '''Make a backup of xorg.conf and return the exit code'''

        self._check_permission(sender, conn,
            'com.ubuntu.screenresolution.mechanism.configure')
        
        xorg_path = '/etc/X11'
        backup_path = os.path.join(xorg_path, backup_file)
        
        try:
            os.unlink(backup_path)
            logging.debug('Removing previous backup: %s' % backup_path)
        except(OSError, IOError):
            logging.debug('Nothing to remove. %s does not exist' % backup_path)
            pass
        
        xorg_source_path = '/etc/X11/xorg.conf'
        
        try:
            #make a backup of the xorg.conf
            shutil.copyfile(xorg_source_path, backup_path)
        except IOError:
            logging.error('%s does not exist' % xorg_source_path)
            return 1
        
        return 0

    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='s', out_signature='i',
                         sender_keyword='sender', connection_keyword='conn')
    def writeXorgConf(self, src_file, sender=None, conn=None):
        '''Validate and copy src_file to xorg.conf and return the exit code'''

        self._check_permission(sender, conn,
            'com.ubuntu.screenresolution.mechanism.configure')
        
        xorg_file_path = '/etc/X11/xorg.conf'
        
        
        try:
            xutils.XUtils(src_file)
            logging.debug('%s is a valid xorg.conf file.' % src_file)
        except(IOError, xorgparser.ParseException):#if xorg.conf is missing or broken
            logging.error('%s does not seem to be a valid xorg.conf file.' % src_file)
            return 1
        
        try:
            shutil.copyfile(src_file, xorg_file_path)
            logging.debug('%s was written successfully to %s.' % (src_file, xorg_file_path))
        except IOError:
            logging.error('%s does not exist' % xorg_source_path)
            return 1
        
        return 0


    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='as', out_signature='i',
                         sender_keyword='sender', connection_keyword='conn')
    def backupAndWriteXorgConf(self, files, sender=None, conn=None):
        '''Make a backup of xorg.conf, validate and copy a file to xorg.conf and return the exit code'''

        try:
            backup_file = files[0]
            src_file = files[1]
        except IndexError:
            logging.error('Invalid arguments.')
            return 1

        self._check_permission(sender, conn,
            'com.ubuntu.screenresolution.mechanism.configure')
        
        xorg_path = '/etc/X11'
        xorg_file_path = os.path.join(xorg_path, 'xorg.conf')
        backup_path = os.path.join(xorg_path, backup_file)

        # Try to remove any previous backup in backup_path        
        try:
            os.unlink(backup_path)
            logging.debug('Removing previous backup: %s' % backup_path)
        except(OSError, IOError):
            logging.debug('Nothing to remove. %s does not exist' % backup_path)
            pass
        
        # Try to make a backup of xorg.conf
        try:
            shutil.copyfile(xorg_file_path, backup_path)
        except IOError:
            logging.debug('%s does not exist' % xorg_file_path)

        # Validate src_file before writing it to xorg.conf
        try:
            xutils.XUtils(src_file)
            logging.debug('%s is a valid xorg.conf file.' % src_file)
        except(IOError, xorgparser.ParseException):#if xorg.conf is missing or broken
            logging.error('%s does not seem to be a valid xorg.conf file.' % src_file)
            return 1
        
        try:
            shutil.copyfile(src_file, xorg_file_path)
            logging.debug('%s was written successfully to %s.' % (src_file, xorg_file_path))
        except IOError:
            logging.error('%s does not exist' % xorg_source_path)
            return 1
        
        return 0
    
def get_service_bus():
    '''Retrieves a reference to the D-BUS system bus.'''

    return dbus.SystemBus()

def get_service(bus=None):
    '''Retrieves a reference to the D-BUS driven configuration service.'''

    if not bus:
        bus = get_service_bus()

    service = bus.get_object(BackendService.SERVICE_NAME, '/')
    service = dbus.Interface(service, BackendService.INTERFACE_NAME)

    return service

if __name__ == '__main__':
    # Support full tracing when --debug switch is passed:
    import sys
    from sys import argv

    # Integrate DBus with GLib main loops.

    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)

    # Run the service.

    if '--debug' in argv or '-d' in argv:
        logging.basicConfig(stream=sys.stderr)
        logging.getLogger().setLevel(logging.NOTSET)
        
    BackendService().run()

