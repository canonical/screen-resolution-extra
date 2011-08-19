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


import gtk, gobject, sys, dbus, logging
import ScreenResolution
from ScreenResolution import ui

SERVICE_NAME   = 'com.ubuntu.ScreenResolution.Mechanism'
OBJECT_PATH    = '/'
INTERFACE_NAME = 'com.ubuntu.ScreenResolution.Mechanism'
usage = 'python policyui.py 1024x768'

import os
import sys
from subprocess import Popen, PIPE

import XKit
from XKit import xutils, xorgparser

clean = False

def checkVirtual(virtres):
    '''See if it's necessary to set the virtual resolution'''

    source = '/etc/X11/xorg.conf'
    
    try:
        a = xutils.XUtils(source)
    except(IOError, XKit.xorgparser.ParseException):#if xorg.conf is missing or broken
        return False
    
    if len(a.globaldict['Screen']) > 0:
        # See if the virtual resolution is already there and if it's big enough
        res = None
        for screen in a.globaldict['Screen']:
            try:
                res = a.getValue('SubSection', 'virtual', 0, identifier='Display', sect="Screen", reference=None)
                if res:
                    if 'x' in res.lower():
                        res = res.lower().split('x')
                    elif ' ' in res.lower().strip():
                        res = res.lower().split(' ')
                        res = filter(lambda x: x != '', res)
                        if len(res) == 2 and int(virtres[0]) <= int(res[0]) and int(virtres[1]) <= int(res[1]):
                            # Nothing to do, the virtual resolution is already there
                            return True
            except (XKit.xorgparser.SectionException, XKit.xorgparser.OptionException, AttributeError):
                pass
    
    return False

def get_xkit_service(widget=None):
    '''
    returns a dbus interface to the screenresolution mechanism
    '''
    service_object = dbus.SystemBus().get_object(SERVICE_NAME, OBJECT_PATH)
    service = dbus.Interface(service_object, INTERFACE_NAME)

    return service

def gui_dialog(message, parent_dialog,
                      message_type=None,
                      widget=None, page=0, 
                      broken_widget=None):
    '''
    Displays an error dialog.
    '''
    if message_type == 'error':
        message_type = gtk.MESSAGE_ERROR
        logging.error(message)
    elif message_type == 'info':
        message_type = gtk.MESSAGE_INFO
        logging.info(message)


    
        
    dialog = gtk.MessageDialog(parent_dialog,
                               gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                               message_type, gtk.BUTTONS_OK,
                               message)
    
    translation = ui.AbstractUI()
    
    dialog.set_title(translation.string_title)
    
    if widget != None:
        if isinstance (widget, gtk.CList):
            widget.select_row (page, 0)
        elif isinstance (widget, gtk.Notebook):
            widget.set_current_page (page)
    if broken_widget != None:
        broken_widget.grab_focus ()
        if isinstance (broken_widget, gtk.Entry):
            broken_widget.select_region (0, -1)

    if parent_dialog:
        dialog.set_position (gtk.WIN_POS_CENTER_ON_PARENT)
        dialog.set_transient_for(parent_dialog)
    else:
        dialog.set_position (gtk.WIN_POS_CENTER)

    ret = dialog.run ()
    dialog.destroy()    

    return ret



class BootWindow:
    optimal_virtual_resolution = ['2048', '2048']
    
    def __init__(self, resolution):
        
        translation = ui.AbstractUI()
        self.permission_text = translation.string_permission_text
        self.dbus_cant_connect = translation.string_dbus_cant_connect
        self.operation_complete = translation.string_operation_complete
        self.cant_apply_settings = translation.string_cant_apply_settings
        
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.on_delete_event)
        self.window.connect("destroy", self.on_destroy)
        
        self.window.set_border_width(20)
        
        self.window.set_title(translation.string_title)
        self.window.set_position(gtk.WIN_POS_CENTER)
        
        self.window.set_icon_from_file("/usr/share/icons/hicolor/16x16/apps/preferences-desktop-display.png")
        
        vbox = gtk.VBox(spacing=20)
        self.resolution = resolution
        self.label = gtk.Label(self.permission_text)
        self.label.set_line_wrap(True)
        self.label.set_justify(gtk.JUSTIFY_FILL)
        self.button1 = gtk.Button(label=None, stock='gtk-yes', use_underline=False)
        self.button1.connect("clicked", self.on_button1_clicked, None)
        self.button1.show()
        self.button2 = gtk.Button(label=None, stock='gtk-no', use_underline=False)
        self.button2.connect("clicked", self.on_button2_clicked, None)
        self.button2.show()
        
        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_END)
        buttonbox.set_spacing(10)
        buttonbox.pack_start(self.button2)
        buttonbox.pack_start(self.button1)
        buttonbox.show()
        vbox.pack_start(self.label)
        vbox.pack_start(buttonbox)
        self.window.add(vbox)
        self.label.show()
        
        vbox.show()
    
    def on_button1_clicked(self, widget, data=None):
        self.window.hide()
        self.conf = get_xkit_service()
        if not self.conf:
#            gui_dialog(self.dbus_cant_connect,
#                              self.window, message_type='error')
            sys.exit(1)
        
        # If the required resolution is lower than the optimal virtual
        # resolution (usually the highest resolution which doesn't break
        # direct rendering) then use the latter instead.
        if int(self.resolution[0]) < int(self.optimal_virtual_resolution[0]) and \
           int(self.resolution[1]) < int(self.optimal_virtual_resolution[1]):
            self.resolution = self.optimal_virtual_resolution

        status = self.conf.setVirtual(self.resolution)
        #print 'Status', status
        if status == True:
            #gui_dialog(self.operation_complete, self.window, message_type='info')
            global clean
            clean = True
            gtk.main_quit()
            #sys.exit(0)

        else:
            #gui_dialog(self.cant_apply_settings, self.window, message_type='error')
            #sys.exit(1)
            gtk.main_quit()
        
    def on_button2_clicked(self, widget, data=None):
        self.window.hide()
#        gui_dialog(self.cant_apply_settings, self.window, message_type='error')
        #sys.exit(1)
        gtk.main_quit()
        
        
    def on_delete_event(self, widget, event, data=None):
        # Close the window:
        return False

    def on_destroy(self, widget, data=None):
        gtk.main_quit()

    def show(self):
       self.window.show()




if __name__ == "__main__":
    if len(sys.argv) > 1:
        for param in sys.argv[1:]:
            if 'x' not in param:
                sys.exit(0)    
    else:
        sys.exit(0)
    
    res = sys.argv[1]
    res = res.strip().split('x')
    if checkVirtual(res):
        sys.exit(0)
    window = BootWindow(res)
    window.show()
    gtk.main()
    if not clean:
        sys.exit(1)
