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

import address
import content


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
            print("Send to "+ self.url +": \n\t" )#+ str(message))
            event.sender.send(message)
            self._message_index += 1
            self._sent_count += 1

    def on_accepted(self, event):
        self._confirmed_count += 1
        if self._confirmed_count == len(self._messages):
            event.connection.close()

    def on_transport_error(self, event):
        raise Exception(event.transport.condition)




if __name__ == "__main__":

    parser = optparse.OptionParser(usage="usage: %prog [options]",
                               description="Send messages to the supplied address.")
    
    parser.add_option("-a", "--address", default=address.url,
                    help="address to which messages are sent (default %default)")

    parser.add_option("-m", "--messages", type="int", default=100,
                    help="number of messages to send (default %default)")

    parser.add_option("-t", "--timeinterval", default=10,
                    help="messages are sent continuosly every time interval seconds (0: send once) (default %default)")

    opts, args = parser.parse_args()
    
    jargs = json.dumps(args)

    print("Sending #" + str(opts.messages) + " messages every " + str(opts.timeinterval) + " seconds to: " + str(opts.address) + "\n" )

    content.messages_generator(opts.messages)

    while(True):
        try:
            Container(Sender(opts.address, content.messages)).run()
            print("... \n")
        except KeyboardInterrupt:
            pass
        if (int(opts.timeinterval) == 0):
            break
        time.sleep(int(opts.timeinterval))