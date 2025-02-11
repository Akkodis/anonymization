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
# Mods by Danilo Amendola
#
# https://qpid.apache.org/releases/qpid-proton-0.31.0/proton/python/docs/proton.html#proton.PropertyDict

from proton import Message
from proton import symbol, ulong, PropertyDict
import base64
import sys

messages = [Message(subject='s%d' % i, body=u'b%d' % i) for i in range(10)]

#
# author: DAmendola
# This method creates a list of messages that will be sent to the Message Broker.
#
def messages_generator(num, tile, image, msgbody=None ):
    messages.clear()

    
    if(msgbody==None):
        with open(image, "rb") as f:
            msgbody = base64.b64encode(f.read())
    
    print("Size of the image: " + str(sys.getsizeof(msgbody)))

    print("Sender prepare the messages... ")
    for i in range(num):        
        props = {
                    "dataType": "image", 
                    "dataSubType": "jpg", 
                    "sourceId": "v"+str(i),
                    "locationQuadkey": tile+str(i%4),
                    "body_size": str(sys.getsizeof(msgbody))
                }

        messages.append( Message(body=msgbody, properties=props) ) 
        #print(messages[i])
    print("Message array done! \n")
