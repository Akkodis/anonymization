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

from __future__ import print_function

from proton.handlers import MessagingHandler
from proton.reactor import Container
import base64
import address

from anonymization import utils
from anonymization.image_processing import Img

import os.path
from object_detection.utils import ops as utils_ops
import tensorflow as tf
import time
import io
import sys

from proton.handlers import MessagingHandler
from proton.reactor import Container
from proton import Message
from datetime import datetime
from getmac import get_mac_address as gma



import os
username=os.environ['AMQP_USER']
password=os.environ['AMQP_PASS']
server=os.environ['AMQP_IP']
port=os.environ['AMQP_PORT']
output_topic=os.environ['TOPIC_WRITE']
instance_type=os.environ['INSTANCE_TYPE']




# patch tf1 into `utils.ops`
utils_ops.tf = tf.compat.v1

# define name of flags
utils_ops.tf.app.flags.DEFINE_string('input_dir', 'res/testimg/input', 'Location of image folder for anonymization')
utils_ops.tf.app.flags.DEFINE_string('output_dir', 'res/testimg/output', 'Location of directory for results')
utils_ops.tf.app.flags.DEFINE_string('model_car_person_dir', 'res/model/car_person/ssd_mobilenet_v1_ppn_shared_box_predictor_300x300_coco14_sync_2018_07_03/saved_model', 'Location of saved_model folder for car and person')
utils_ops.tf.app.flags.DEFINE_string('model_face_license_dir', 'res/model/face_license/face_license/saved_model', 'Location of saved_model folder for face and license')
utils_ops.tf.app.flags.DEFINE_float('threshold', '0.2', 'Value of detection threshold,default is 0.2', lower_bound=0.0, upper_bound=1.0)
utils_ops.tf.app.flags.DEFINE_bool('detail', 'False', 'Save output for each process during the detection')
FLAGS = utils_ops.tf.app.flags.FLAGS

# patch the location of gfile
tf.gfile = tf.io.gfile

model_car_person_dir=FLAGS.model_car_person_dir
model_face_license_dir=FLAGS.model_face_license_dir
threshold=FLAGS.threshold
detail=FLAGS.detail
input_dir=FLAGS.input_dir
output_dir=FLAGS.output_dir

model_car_person = utils.save_load.load_model(model_car_person_dir)
model_face_license = utils.save_load.load_model(model_face_license_dir)






#import address


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
        #print("SENDER CREATED")

    def on_sendable(self, event):
        #print(event.sender.credit)
        while event.sender.credit and self._sent_count < len(self._messages):
            message = self._messages[0]
            event.sender.send(message)
            self._message_index += 1
            self._sent_count += 1

    def on_accepted(self, event):
        self._confirmed_count += 1
        #print("msg accepted")
        #if self._confirmed_count == len(self._messages):
        event.connection.close()

    def on_transport_error(self, event):
        raise Exception(event.transport.condition)


def anonymization_process(model_car_person_dir,
                          model_face_license_dir,
                          threshold,
                          detail,
                          input_dir,
                          output_dir):

    TEST_IMAGE_PATHS = utils.save_load.get_image_paths(input_dir)
    model_car_person = utils.save_load.load_model(model_car_person_dir)
    model_face_license = utils.save_load.load_model(model_face_license_dir)

    counter = 0
    start = time.time()

    for img_path in TEST_IMAGE_PATHS:
        input_img = Img(img_path)
        name = os.path.splitext(os.path.basename(img_path))[0]
        input_img.detection_car_person(model_car_person)
        input_img.detection_face_license(model_face_license, threshold)
        blurred_img = input_img.blurring()

        # save anonymiazed results
        utils.save_load.save_image(blurred_img, name, output_dir + 'anonymized/')
        counter += 1

    end = time.time()
    print(counter, 'images was anonymized')
    print('total time cost:% .2f s' % (end-start))
    print('average time cost: % .2f s' % ((end-start)/counter))


#def main(_):
#    anonymization_process(
#      model_car_person_dir=FLAGS.model_car_person_dir,
#      model_face_license_dir=FLAGS.model_face_license_dir,
#      threshold=FLAGS.threshold,
#      detail=FLAGS.detail,
#      input_dir=FLAGS.input_dir,
#      output_dir=FLAGS.output_dir)


#if __name__ == '__main__':
#    utils_ops.tf.app.run()




class Receiver(MessagingHandler):
    def __init__(self, url, messages_to_receive=10):
        super(Receiver, self).__init__()
        self.url = url
        self._messages_to_receive = messages_to_receive
        self._messages_actually_received = 0
        self._stopping = False
        self._instance_type= instance_type
        self._counter = 0

    def on_start(self, event):
        event.container.create_receiver(self.url)

    def on_message(self, event):
        if self._stopping:
            return
        self._counter +=1
        
        # Subsampling block
        if self._instance_type == "small":
            if self._counter % 10 == 0:
                pass
            else: 
                #print("small, no execution")
                return
        if self._instance_type == "medium":
            if self._counter % 5 == 0:
                pass
            else: 
                #print("medium, no execution")
                return
        if self._instance_type == "large":
                #print("large, no execution")
                pass
        if self._instance_type == "advanced":
                #print("advanced, no execution")
                pass
        
                    
        #print("Executing "+str(self._counter))
        url='amqp://'+username+':'+password+'@'+server+':'+port+'/topic://'+output_topic
        model_car_person_dir=FLAGS.model_car_person_dir
        model_face_license_dir=FLAGS.model_face_license_dir
        threshold=FLAGS.threshold
        detail=FLAGS.detail
        input_dir=FLAGS.input_dir
        output_dir=FLAGS.output_dir


        #print(event.message)
        decoded=base64.b64decode(event.message.body)
        input_img = Img(decoded)
        c=event.message.body
        try:
            input_img.detection_car_person(model_car_person)
            input_img.detection_face_license(model_face_license, threshold)
            blurred_img = input_img.blurring()
            bytes=io.BytesIO()
            blurred_img.save(bytes,format="JPEG")
            blur_im_data=bytes.getbuffer()
            c=base64.b64encode(blur_im_data)
        except:
            print("Error, passing original")

        #c=c.hex()
        props = {
                    "dataType": event.message.properties['dataType'], 
                    "dataSubType": event.message.properties['dataSubType'], 
                    "sourceId": event.message.properties['sourceId'], 
                    "locationQuadkey":event.message.properties['locationQuadkey'],
                    "body_size": str(sys.getsizeof(c))
                }

        message=Message(body=c, properties=props)#b'\xd1\x144S+')#'bbb')#img.image_data)
        #self.sender=Sender(self.url, [message])
        #self.container=Container(self.sender)
        #self.container
        Container(Sender(url, [message])).run()



        # save anonymiazed results
        #utils.save_load.save_image(blurred_img, str(self._messages_actually_received)+".jpg", output_dir + 'anonymized/')


        #file=open(str(self._messages_actually_received)+".jpg","wb")
        #file.write(image)
        #file.close()
        print(str(self._messages_actually_received)+" images blurred")
        self._messages_actually_received += 1
        #if self._messages_actually_received == self._messages_to_receive:
        #    event.connection.close()
        #    self._stopping = True

    def on_transport_error(self, event):
        raise Exception(event.transport.condition)


if __name__ == "__main__":
    try:
        Container(Receiver(address.url)).run()
    except KeyboardInterrupt:
        pass
