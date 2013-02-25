#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2013 KNX-User-Forum e.V.            http://knx-user-forum.de/
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
#  along with SmartHome.py. If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import logging

from threading import currentThread
from twisted.internet import reactor, ssl
from proxy import SiriProxyFactory

logger = logging.getLogger('')


class Siri():

    def __init__(self, smarthome):
        self._sh = smarthome
        self._items = []
        self._logics = []

    def run(self):
        self.alive = True

        settings = []
        settings['smarthome'] = self._sh
        settings['root'] = os.path.realpath(__file__)
        settings['items'] = self._items
        settings['logics'] = self._logics
        ## Start the Proxy
        logger.info('Starting SiriProxy')
        reactor.listenSSL(443, SiriProxyFactory(**settings),
            ssl.DefaultOpenSSLContextFactory(
                os.path.join(os.path.realpath(__file__), 'certificates', 'server.key'),
                os.path.join(os.path.realpath(__file__), 'certificates', 'server.crt')
            )
        )
        reactor.run()

    def stop(self):
        self.alive = False
        reactor.stop()
        if currentThread().getName() == 'MainThread':
            # Code is running in the main reactor thread
            reactor.stop()
        else:
            # Code is running in a child thread
            reactor.callFromThread(reactor.stop)

    def parse_item(self, item):
        if 'siri' in item.conf:
            logger.debug("parse item: {0}".format(item))
            self._items.append((item, item.conf['siri']))
        
        return None

    def parse_logic(self, logic):
        if 'siri' in logic.conf:
            self._logics.append((logic, logic.conf['siri']))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    siri = SiriProxy('smarthome-dummy')
    siri.run()
