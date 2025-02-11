#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
#
# Author: D.Amendola
# Useful resources: 
#   https://qpid.apache.org/releases/qpid-proton-0.36.0/proton/python/docs/tutorial.html
#   https://access.redhat.com/documentation/en-us/red_hat_amq/6.3/html/client_connectivity_guide/amqppython

from __future__ import print_function

import optparse
import json
import time
from proton.handlers import MessagingHandler
from proton.reactor import Container
import os

import content

import discovery_registration
from pygeotile.tile import Tile


# Geoposition - Next steps: from GPS device. Now hardcoded.
# Put your position here
latitude    = 43.2952
longitude    = -1.9850

tileTmp = Tile.for_latitude_longitude(latitude=latitude, longitude=longitude, zoom=18)
tile=str(tileTmp.quad_tree)
username="5gmeta-user"
password="5gmeta-password"
timeinterval=10
messages=1
folder_path="sample_images"
dir_path = r'sample_images'



# Replace with your metadata
dataflowmetadata = {
    "dataTypeInfo": {
        "dataType": "image",
        "dataSubType": "cam"
    },
    "dataInfo": {
        "dataFormat": "asn1_jer",
        "dataSampleRate": 0.0,
        "dataflowDirection": "upload",
        "extraAttributes": None,
    },
    "licenseInfo": {
        "licenseGeolimit": "europe",
        "licenseType": "profit"
    },
    "dataSourceInfo": {
        "sourceTimezone": 2,
        "sourceStratumLevel": 1,
        "sourceId": 1,
        "sourceType": "vehicle",
        "sourceLocationInfo": {
            "locationQuadkey": tile,
            "locationCountry": "ESP",
            "locationLatitude": latitude,
            "locationLongitude": longitude
        }
    }   
}


class Sender(MessagingHandler):
    def __init__(self, url, messages):
        super(Sender, self).__init__()
        self.url = url
        self._messages = messages
        self._message_index = 0
        self._sent_count = 0
        self._confirmed_count = 0

    def on_start(self, event):
        event.container.create_sender(self.url)

    def on_sendable(self, event):
        while event.sender.credit and self._sent_count < len(self._messages):
            message = self._messages[self._message_index]
            event.sender.send(message)
            self._message_index += 1
            self._sent_count += 1
            event.sender.close()

    def on_accepted(self, event):
        self._confirmed_count += 1
        if self._confirmed_count == len(self._messages):
            event.connection.close()

    def on_transport_error(self, event):
        raise Exception(event.transport.condition)




if __name__ == "__main__":

    # Get Message Broker access
    service="message-broker"
    messageBroker_ip, messageBroker_port = discovery_registration.discover_sb_service(tile,service)
    if messageBroker_ip == -1 or messageBroker_port == -1:
        print(service+" service not found")
        exit(-1)
    
    # Get Topic and dataFlowId to push data into the Message Broker
    dataflowId, topic = discovery_registration.register(dataflowmetadata,tile)

    print("dataflow id is "+str(dataflowId))

    address="amqp://"+username+":"+password+"@"+messageBroker_ip+":"+str(messageBroker_port)+"/topic://"+topic

 

    print("Sending #" + str(1) + " messages every " + str(timeinterval) + " seconds to: " + str(address) + "\n" )

    for path in os.listdir(dir_path):
        # check if current path is a file
        if os.path.isfile(os.path.join(dir_path, path)):
            content.messages_generator(messages,tile,"./"+folder_path+"/"+path)
            try:
                Container(Sender(address, content.messages)).run()
                discovery_registration.keepAliveDataflow(dataflowmetadata,dataflowId)
                print("... \n")
            except KeyboardInterrupt:
                pass
            if (int(timeinterval) == 0):
                break
            time.sleep(int(timeinterval))