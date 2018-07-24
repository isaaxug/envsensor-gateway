from logging import getLogger

logger = getLogger(__name__)

from flask import Flask, render_template
from flask_sockets import Sockets
import geventwebsocket.exceptions
import json
import random
import uuid

try:
    from queue import Queue, Empty, Full
except ImportError:
    from Queue import Queue, Empty, Full

app = Flask(__name__)
sockets = Sockets(app)

@sockets.route('/talk/<address>')
def talk(ws, address):
    logger.debug('[request] address is %s', address)
    queue = Queue(maxsize=10)

    try:
        uId = o.setRequest(address, queue)

        while not ws.closed:
            json_string = queue.get(block=True)
            ws.send(json_string)

    except geventwebsocket.exceptions.WebSocketError as e:
        logger.debug('connection lost')
        print(e)

    except Exception as e:
        logger.exception(e)

    finally:
        o.rmRequest(uId)

    logger.debug('end')

@app.route('/devices')
def findDevices():
    return json.dumps(list(o.getCurrentDevices()))


@app.route('/')
def hello():
    return render_template('index.html')


from omron_envsensor import OmronEnvSensor
from omron_envsensor.sensorbeacon import csv_header
from omron_envsensor.util import getHostname
import sys
import os

BLUETHOOTH_DEVICEID = os.environ.get('BLUETHOOTH_DEVICEID', 0)

from threading import Thread
import time

ADDRESSESS_KEEPALIVE = 10

class EnvTread(Thread):
    filters = {}
    active_devices = {}

    def __init__(self, hostname=None, bt=0, daemon=True, *args, **kwargs):
        if hostname is None:
            hostname = getHostname()

        self.omron = OmronEnvSensor(hostname, bt)
        self.omron.on_message = self.callback

        super(EnvTread, self).__init__(daemon=daemon, *args, **kwargs)

    def run(self):
        logger.debug('omron start')
        self.omron.init()
        try:
            self.omron.loop()
        except Exception as e:
            logger.exception(e)

    def setRequest(self, address, queue):
        uId = str(uuid.uuid4())
        self.filters[uId] = (address, queue)
        logger.debug('filters is %s', self.filters)
        return uId

    def rmRequest(self, uId):
        try:
            del self.filters[uId]
        except Exception as e:
            logger.exception(e)

        logger.debug('filters is %s', self.filters)

    def callback(self, beacon):
        address = beacon.bt_address.replace(':', '').upper()
        logger.debug('get beacon %s', address)
        self.addDevice(address)
        for k, i in self.filters.items():
            logger.debug(i)
            if i[0] == address:
                logger.debug('hit!')
                i[1].put(beacon.json_format())

    def addDevice(self, address):
        now = time.time()
        self.active_devices[address] = now

        if 1 > random.choice([i for i in range(0, 10)]):
            self.refreshDevices()


    def refreshDevices(self):
        now = time.time()
        removes = []
        for i in self.active_devices.keys():
            if now > self.active_devices[i] + ADDRESSESS_KEEPALIVE:
                removes.append(i)

        for i in removes:
            del self.active_devices[i]
        logger.debug('current devices is %s', self.active_devices)

    def getCurrentDevices(self):
        self.refreshDevices()
        return self.active_devices.keys()

if __name__ == "__main__":
    import logging

    rootLogger = logging.getLogger(__name__)
    rootLogger.addHandler(logging.StreamHandler())
    rootLogger.setLevel(logging.DEBUG)


    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    o = EnvTread(bt=BLUETHOOTH_DEVICEID)
    o.start()
    server.serve_forever()
