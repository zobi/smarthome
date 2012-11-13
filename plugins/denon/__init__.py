#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2012 KNX-User-Forum e.V.            http://knx-user-forum.de/
#########################################################################
#  This file is part of SmartHome.py.   http://smarthome.sourceforge.net/
#
#  SmartHome.py is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SmartHome.py is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHome.py.  If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import logging
import socket
import threading
import struct
import time

import lib.my_asynchat

logger = logging.getLogger('')

DELIMITER = '\r'

class Denon(lib.my_asynchat.AsynChat):

    def __init__(self, smarthome, host, port=23):
        lib.my_asynchat.AsynChat.__init__(self, smarthome, host, port)
        self.terminator = DELIMITER
        self._sh = smarthome
        self.commands = {}
        self._supported = ['PW', 'MV', 'MU', 'SI', 'SV', 'SLP', 'TFANUP', 'TFANDOWN', 'TP', 'TM']
        self._si = ['CD', 'TUNER', 'DVD', 'BD', 'TV', 'SAT/CBL', 'MPLAY', 'GAME', 'AUX1', 'NET', 'PANDORA', 'SIRIUSXM', 'LASTFM', 'FLICKR', 'FAVORITES', 'IRADIO', 'SERVER', 'USB/IPOD', 'USB', 'IPD', 'IRP', 'FVP']
        self._sv = ['DVD', 'BD', 'TV', 'SAT/CBL', 'MPLAY', 'GAME', 'AUX1', 'CD', 'SOURCE']
        smarthome.monitor_connection(self)

    def collect_incoming_data(self, data):
        print data
        self.buffer += data

    def parse_item(self, item):
        if 'denon_cmd' in item.conf:
            cmd = item.conf['denon_cmd']
        else:
            return None

        opt = None
        if 'denon_opt' in item.conf:
            opt = item.conf['denon_opt']

            if opt == 'UP/DOWN':
                item._enforce_updates = True
        
        # add only supported commands
        # this type of commands are updated from this plugin
        # all other commands only can be send by this plugin
        for key in self._supported:
            if cmd.startswith(key):
                self.commands[cmd] = { 'item': item, 'opt': opt }
                logger.debug("Supported command {0} for item {1} added".format(cmd, item))
                return self.update_item

        logger.debug("Command {0} on item {1} found".format(cmd, item))

        if item._enforce_updates is False:
            logger.warning("Updates are not enforced on item {0}, you should consider enforcing updates by setting enforce_updates = True")

        return self.update_item

    def parse_logic(self, logic):
        pass

    def update_item(self, item, caller=None, source=None):
        if caller != 'Denon':
            cmd = item.conf['denon_cmd']

            if cmd not in self.commands:
                self.send(cmd)
                return

            cmd_obj = self.commands[cmd]
            opt = cmd_obj['opt']
            
            if cmd == 'PW':
                self.send(cmd, 'ON' if item() else 'STANDBY')
            elif cmd == 'MV':
                if opt == None:
                    self.send(cmd, '{0:X}'.format(int(round(float(item()) / 255.0 * 152.0))))
                elif item()[1] != 0:
                    self.send(cmd, 'UP' if item()[0] == 1 else 'DOWN')
            elif cmd == 'MU':
                self.send(cmd, 'ON' if item() else 'OFF')
            elif cmd == 'SI':
                self.send(cmd, self._si[item()])
            elif cmd == 'SV':
                self.send(cmd, self._sv[item()])
            elif cmd == 'SLP':
                self.send(cmd, 'OFF' if item() == 0 else str(min(item(), 120)).zfill(3))

            # Tuner Commands
            elif cmd == 'TFANUP' or cmd == 'TFANDOWN' or cmd == 'TPANUP' or cmd == 'TPANDOWN':
                self.send(cmd)
            elif cmd == 'TMAN':
                self.send(cmd, 'AUTO' if item() else 'MANUAL')
            elif cmd == 'TPAN':
                self.send(cmd, '{0:X}'.format(min(item(), 55) + 161))

    def send(self, cmd, param=''):
        logger.debug("Sending request: {0}{1}".format(cmd, param))
        self.push('{0}{1}\r'.format(cmd, param))

    def _parse_response(self, resp):
        try:
            logger.debug("Parse response: {0}".format(resp))

            for key in self.commands:
                if resp.startswith(key):
                    value = self._decode(key, resp[len(key):])
                    if value == None:
                        return

                    self.commands[key]['item'](value, 'Denon')
                    return

        except Exception, e:
            logger.error(e)

    def _decode(self, cmd, value):
        if cmd == 'PW':
            return value == 'ON'
        elif cmd == 'MV':
            return int(round(float(hex(value)) / 152.0 * 255.0))
        elif cmd == 'MU':
            return value == 'ON'
        elif cmd == 'SI':
            return self._si.index(value)
        elif cmd == 'SV':
            return self._sv.index(value)
        elif cmd == 'SLP':
            value = int(value)
            return 'OFF' if value == 0 else value

        # Tuner Commands
        elif cmd == 'TMAN':
            return value == 'TMANAUTO'
        elif cmd == 'TPAN':
            value = value[4:]
            if value == 'OFF':
                return None
            else:
                return int(hex(value)) - 161
                
    def found_terminator(self):
        data = self.buffer
        self.buffer = ''
        self._parse_response(data)

    def handle_connect(self):
        self.terminator = DELIMITER
        print self.commands
        for cmd in self.commands:
            print "command is " + cmd
            self.send(cmd, '?')

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False
        self.handle_close()
