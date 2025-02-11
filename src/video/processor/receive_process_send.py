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

#from PIL import Image, ImageFilter

import threading
import numpy

import gi

gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gst, GObject, GLib, GstApp, GstVideo

import content

ids = []
dec_framerates = []
enc_framerates = []
tiles = []
dec_ptss = []
enc_ptss = []
dec_durations = []
enc_durations = []
encoders = []
decoders = []
dec_w_imgs = []
dec_h_imgs = []
enc_w_imgs = []
enc_h_imgs = []
out_fps = ''
out_width = ''
out_height = ''


import os
# Get all environmental variables
username=os.getenv('AMQP_USER')
password=os.getenv('AMQP_PASS')
server=os.getenv('AMQP_IP')
port=os.getenv('AMQP_PORT')
topic_read=os.getenv('TOPIC_READ')
topic_write=os.getenv('TOPIC_WRITE')
enableNV=os.getenv('ENABLE_NV')
instance_type=os.getenv('INSTANCE_TYPE')

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

# Set paths
model_car_person_dir=FLAGS.model_car_person_dir
model_face_license_dir=FLAGS.model_face_license_dir
threshold=FLAGS.threshold
detail=FLAGS.detail
input_dir=FLAGS.input_dir
output_dir=FLAGS.output_dir

# Set vehicular plate and face ML models to blur
model_car_person = utils.save_load.load_model(model_car_person_dir)
model_face_license = utils.save_load.load_model(model_face_license_dir)

# Class to send ingress anonymized messages
class Sender(MessagingHandler):
    def __init__(self, url, message):
        super(Sender, self).__init__()
        self.url = url
        self._message = message
        self._sent_count = 0
        self._confirmed_count = 0

    def on_start(self, event):
        #print("Sender Created")
        event.container.create_sender(self.url)

    def on_sendable(self, event):
        message = self._message
        #print("Send to "+ self.url +": \n\t" )#+ str(message))
        event.sender.send(message)
        self._sent_count += 1
        event.sender.close()

    def on_accepted(self, event):
        self._confirmed_count += 1
        event.connection.close()

    def on_transport_error(self, event):
        raise Exception(event.transport.condition)

# Transform video frame data buffer
def ndarray_to_gst_buffer(array: numpy.ndarray) -> Gst.Buffer:
    """Converts numpy array to Gst.Buffer"""
    return Gst.Buffer.new_wrapped(array.tobytes())

# Callback for each decoded video frame
def on_buffer(sink, data):
    global ids
    global dec_ptss
    global enc_ptss
    global dec_durations
    global enc_durations
    global dec_framerates
    global enc_framerates
    global tiles
    global decoders
    global encoders
    global dec_w_imgs
    global dec_h_imgs
    global enc_w_imgs
    global enc_h_imgs
    """Callback on 'new-sample' signal"""
    # Emit 'pull-sample' signal
    # https://lazka.github.io/pgi-docs/GstApp-1.0/classes/AppSink.html#GstApp.AppSink.signals.pull_sample
    sample = sink.emit("pull-sample")  # Gst.Sample

    if isinstance(sample, Gst.Sample):
        index = ids.index(data.id)
        if sink == (decoders[index]).appsink :
            # Prepare raw video frame to be anonymised
            
            # Get the image size parameters
            caps = sample.get_caps()
            # Extract the width and height info from the sample's caps
            h_img = caps.get_structure(0).get_value("height")
            w_img = caps.get_structure(0).get_value("width")
            dec_w_imgs[index] = w_img
            dec_h_imgs[index] = h_img
            enc_w_imgs[index] = w_img
            enc_h_imgs[index] = h_img
            print("\tDecoded[%d]: %d x %d" % (data.id, w_img, h_img))

            # Get the actual data
            buffer = sample.get_buffer()
            # Get read access to the buffer data
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if not success:
                raise RuntimeError("Could not map buffer data!")

            # Transform colorspace and byte structure to enable ML processing
            numpy_frame = numpy.ndarray(
                shape=(h_img, w_img, 3),
                dtype=numpy.uint8,
                buffer=map_info.data)

            # Clean up the buffer mapping
            buffer.unmap(map_info)

            # Set ML models to apply
            model_car_person_dir=FLAGS.model_car_person_dir
            model_face_license_dir=FLAGS.model_face_license_dir
            threshold=FLAGS.threshold
            detail=FLAGS.detail
            input_dir=FLAGS.input_dir
            output_dir=FLAGS.output_dir

            # Process decoded/raw video frame
            input_img = Img(numpy_frame)
            aux = numpy.asarray(numpy_frame)
            try:
                input_img.detection_car_person(model_car_person)
                input_img.detection_face_license(model_face_license, threshold)
                blurred_img = input_img.blurring()
                image_blurred = numpy.asarray(blurred_img)
                aux = image_blurred
            except:
                print("Error, passing original")                
            #print("\tSize Anonymised Buffer:%d %d %d %d" % (int(len(aux)), aux.shape[0], aux.shape[1], aux.shape[2]))
            # Prepare anonymised video frame (raw) to be encoded in H.264
            gst_buffer = Gst.Buffer.new_allocate(None, int(aux.shape[0]*aux.shape[1]*aux.shape[2]), None) 
            gst_buffer.fill(0, aux.tobytes())

            # set pts and duration to be able to record video, calculate fps
            gst_buffer.pts = enc_ptss[index]
            enc_ptss[index] = enc_ptss[index] + enc_durations[index]  # Increase pts by duration
            gst_buffer.duration = enc_durations[index]

            # emit <push-buffer> event with Gst.Buffer
            if ((encoders[index]).appsrc != None) and ((encoders[index]).playing == True):
                print("\tPushed GstBuffer to Encoder [%d] pts:%d duration:%d" % (data.id, gst_buffer.pts, gst_buffer.duration))
                (encoders[index]).appsrc.emit("push-buffer", gst_buffer)

        elif sink == (encoders[index]).appsink :
            # Prepare anonymised encoded video frame to be reinyected in the corresponding AMQP topic

            # Get Gst Buffer
            buffer = sample.get_buffer()  # Gst.Buffer

            # Get caps (resolution, format, fps,...)
            caps = sample.get_caps()  # Gst.Caps

            # Get buffer size
            buffer_size = buffer.get_size()
            # Marshall Gst buffer in a format ready to be sent through AMQP
            array = numpy.ndarray((buffer_size, 1, 1), buffer=buffer.extract_dup(0, buffer_size), dtype=numpy.uint8)

            # Prepare de AMQP message
            content.message_generator(data.id, data.fps, data.tile, array.tobytes())
            server_url = 'amqp://'+username+':'+password+'@'+server+':'+port+'/topic://'+topic_write
            print ("\t\tSend Anonymised Buffer [%d:%s]\n" % (data.id, data.fps))
            # Send anonymised and encoded video frame
            Container(Sender(server_url, content.message)).run()

        return Gst.FlowReturn.OK

    return Gst.FlowReturn.ERROR


# Once video frame is anonymised let's encode
class VIDEO2AMQP(threading.Thread):
    
    def __init__(self, id, fps, tile) :
        super().__init__()
        self._kill = threading.Event()

        self.id = id
        self.fps = fps
        self.tile = tile

        self.playing = False

        self.msg = None
        self.pipeline = None
        self.bus = None
        self.appsink = None
        self.appsrc = None

    def run(self):
        global ids
        global dec_ptss
        global enc_ptss
        global dec_durations
        global enc_durations
        global dec_framerates
        global enc_framerates
        global tiles
        global decoders
        global encoders
        global dec_w_imgs
        global dec_h_imgs
        global enc_w_imgs
        global enc_h_imgs
        print ("\n\n\t\tRUN ENCODER[%d]!\n\n" % (self.id))
        
        index = ids.index(self.id)
        while (dec_w_imgs[index] == 0) or (dec_h_imgs[index] == 0):
                time.sleep(1.0/dec_framerates[index])

        # Set default quality and data sampling rate (fps) to save processing capacity
        bitrate = 1000
        if (enc_framerates[index] <= 2.0) or ((enc_w_imgs[index] <= 640) and (enc_h_imgs[index] <= 480)):
            bitrate = 500

        # build the pipeline
        if enableNV == 'True':
            # HW accelerated encoding
            self.pipeline = Gst.parse_launch(
                'appsrc caps="video/x-raw, format=RGB, width=%d, height=%d" name=appsrc ! videoconvert ! queue max-size-buffers=1 ! queue max-size-buffers=1 ! nvh264enc bitrate=%d name=encoder preset=low-latency-hp zerolatency=true gop-size=5 rc-mode=cbr-ld-hq ! video/x-h264,profile=baseline ! h264parse config-interval=-1 ! video/x-h264, stream-format=byte-stream, alignment=au ! appsink emit-signals=true name=appsink' % (enc_w_imgs[index], enc_h_imgs[index], bitrate)
            )
        else:
            # SW encoding
            self.pipeline = Gst.parse_launch(
                'appsrc caps="video/x-raw, format=RGB, width=%d, height=%d" name=appsrc ! videoconvert ! queue max-size-buffers=1 ! queue max-size-buffers=1 ! x264enc bitrate=%d speed-preset=ultrafast tune=zerolatency key-int-max=5 ! video/x-h264,profile=constrained-baseline ! h264parse config-interval=-1 ! video/x-h264, stream-format=byte-stream, alignment=au ! appsink emit-signals=true name=appsink' % (enc_w_imgs[index], enc_h_imgs[index], bitrate)
            )

        self.appsrc = self.pipeline.get_by_name("appsrc")  # get AppSrc
        # instructs appsrc that we will be dealing with timed buffer
        self.appsrc.set_property("format", Gst.Format.TIME)

        # instructs appsrc to block pushing buffers until ones in queue are preprocessed
        # allows to avoid huge queue internal queue size in appsrc
        self.appsrc.set_property("block", True)

        self.appsink = self.pipeline.get_by_name('appsink')  # get AppSink
        # subscribe to <new-sample> signal
        self.appsink.connect("new-sample", on_buffer, self)

        # start playing
        self.playing = True
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("Unable to set the pipeline to the playing state.")
            exit(-1)


        # wait until EOS or error
        self.bus = self.pipeline.get_bus()

        # Parse message
        while True:
            self.msg = self.bus.timed_pop_filtered(10000, Gst.MessageType.ANY)
            if self.msg:
                if self.msg.type == Gst.MessageType.ERROR:
                    err, debug = self.msg.parse_error()
                    print(("Error received from element %s: %s" % (
                        self.msg.src.get_name(), err)))
                    print(("Debugging information: %s" % debug))
                    break
                elif self.msg.type == Gst.MessageType.EOS:
                    print("End-Of-Stream reached.")
                    break
                elif self.msg.type == Gst.MessageType.STATE_CHANGED:
                    if isinstance(self.msg.src, Gst.Pipeline):
                        old_state, new_state, pending_state = self.msg.parse_state_changed()
                        print(("Pipeline state changed from %s to %s." %
                            (old_state.value_nick, new_state.value_nick)))
                else:
                    print("Unexpected message received.")
            time.sleep(1.0/float(self.fps))

        # free resources
        self.pipeline.set_state(Gst.State.NULL)

    def kill(self):
        self._kill.set()

# Once video frame is coming let's decode and anonymise
class AMQP2VIDEO(threading.Thread):
    
    def __init__(self, id, fps, tile) :
        super().__init__()
        self._kill = threading.Event()

        self.id = id
        self.fps = fps
        self.tile = tile

        self.playing = False

        self.msg = None
        self.pipeline = None
        self.bus = None
        self.appsink = None
        self.appsink = None
        self.appsrc = None


    def run(self):
        global ids
        global dec_ptss
        global enc_ptss
        global dec_durations
        global dec_framerates
        global tiles
        global decoders
        global encoders
        global dec_w_imgs
        global dec_h_imgs
        global enc_w_imgs
        global enc_h_imgs
        global out_fps
        global out_width
        global out_height

        print ("\n\n\t\tRUN DECODER[%d]!\n\n" % (self.id))

        # build the pipeline to decode
        if(out_fps == '0') and (out_width == '0') and (out_height == '0'):
            self.pipeline = Gst.parse_launch(
                'appsrc caps="video/x-h264, stream-format=byte-stream, alignment=au" name=appsrc ! h264parse config-interval=-1 ! decodebin ! videoconvert ! video/x-raw, format=RGB ! appsink emit-signals=true name=appsink'
            )
        else:
            self.pipeline = Gst.parse_launch(
                'appsrc caps="video/x-h264, stream-format=byte-stream, alignment=au" name=appsrc ! h264parse config-interval=-1 ! decodebin ! videorate ! videoscale ! videoconvert ! video/x-raw, framerate=%d/1, width=%d, height=%d, format=RGB ! appsink emit-signals=true name=appsink' % (int(out_fps), int(out_width), int (out_height))
            )

        self.appsrc = self.pipeline.get_by_name("appsrc")  # get AppSrc
        # instructs appsrc that we will be dealing with timed buffer
        self.appsrc.set_property("format", Gst.Format.TIME)

        # instructs appsrc to block pushing buffers until ones in queue are preprocessed
        # allows to avoid huge queue internal queue size in appsrc
        self.appsrc.set_property("block", True)

        self.appsink = self.pipeline.get_by_name('appsink')  # get AppSink
        # subscribe to <new-sample> signal
        self.appsink.connect("new-sample", on_buffer, self)

        # start playing
        self.playing = True
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("Unable to set the pipeline to the playing state.")
            exit(-1)

        # wait until EOS or error
        self.bus = self.pipeline.get_bus()

        # Parse message
        while True:
            self.msg = self.bus.timed_pop_filtered(10000, Gst.MessageType.ANY)
            if self.msg:
                if self.msg.type == Gst.MessageType.ERROR:
                    err, debug = self.msg.parse_error()
                    print(("Error received from element %s: %s" % (
                        self.msg.src.get_name(), err)))
                    print(("Debugging information: %s" % debug))
                    break
                elif self.msg.type == Gst.MessageType.EOS:
                    print("End-Of-Stream reached.")
                    break
                elif self.msg.type == Gst.MessageType.STATE_CHANGED:
                    if isinstance(self.msg.src, Gst.Pipeline):
                        old_state, new_state, pending_state = self.msg.parse_state_changed()
                        print(("Pipeline state changed from %s to %s." %
                            (old_state.value_nick, new_state.value_nick)))
                else:
                    print("Unexpected message received.")
            time.sleep(1.0/float(self.fps))

        # free resources
        self.pipeline.set_state(Gst.State.NULL)

    def kill(self):
        self._kill.set()

# Receive unanonymised video frames inside AMQP messages
class Receiver(MessagingHandler):
    def __init__(self, url):
        super(Receiver, self).__init__()
        self.url = url
        self._messages_actually_received = 0
        self._stopping = False

    def on_start(self, event):
        event.container.create_receiver(self.url)

    def on_message(self, event):
        global ids
        global dec_ptss
        global enc_ptss
        global dec_durations
        global enc_durations
        global dec_framerates
        global enc_framerates
        global tiles
        global decoders
        global encoders
        global dec_w_imgs
        global dec_h_imgs
        global enc_w_imgs
        global enc_h_imgs
        global out_fps
        global out_width
        global out_height

        if self._stopping:
            return

        print(
            "Received frame Content-Type[%d]: video/x-h264 of size:%s" % (event.message.properties['sourceId'], event.message.properties['body_size']))
        if event.message.properties['sourceId'] in ids:
            index = ids.index(event.message.properties['sourceId'])
            decoder = decoders[index]
        else:
            print("\n\nCREATE PIPELINES TO PROCESS [%d]\n\n" % (event.message.properties['sourceId']))
            ids.append(event.message.properties['sourceId'])
            index = ids.index(event.message.properties['sourceId'])
            dec_ptss.append(0)
            enc_ptss.append(0)
            dec_w_imgs.append(0)
            dec_h_imgs.append(0)
            enc_w_imgs.append(0)
            enc_h_imgs.append(0)
            enc_framerates.append(0.0)
            enc_durations.append(0)
            dec_framerates.append(float(event.message.properties['dataSampleRate']))
            dec_durations.append(10**9 / (int(float(event.message.properties['dataSampleRate']) / 1.0)))
            tiles.append(event.message.properties['locationQuadkey'])

            print("\n\n\tINSTANCE_TYPE\n\n", file=sys.stderr)
            print(instance_type, file=sys.stderr)
            print("\n\n\t-------------\n\n", file=sys.stderr)

            # Subsampling block depending on the Instance type
            if instance_type == "small":
                out_fps = '1'
                out_width = '320'
                out_height = '240'
            elif instance_type == "medium":
                out_fps = '2'
                out_width = '640'
                out_height = '480'
            elif instance_type == "large":
                out_fps = '0'
                out_width = '640'
                out_height = '480'
            elif instance_type == "advanced":
                out_fps = '0'
                out_width = '0'
                out_height = '0'
            else:
                out_fps = '1'
                out_width = '320'
                out_height = '240'

            # Trigger the encoder and message sending
            if(out_fps == '0'):
                encoder = VIDEO2AMQP(event.message.properties['sourceId'], event.message.properties['dataSampleRate'], event.message.properties['locationQuadkey'])
                enc_durations[index] = 10**9 / (int(float(event.message.properties['dataSampleRate']) / 1.0))
            else:
                encoder = VIDEO2AMQP(event.message.properties['sourceId'], out_fps, event.message.properties['locationQuadkey'])
                enc_durations[index] = 10**9 / (int(float(out_fps) / 1.0))
            if(out_width == '0') and (out_height == '0'):
                enc_w_imgs[index] = int(out_width)
                enc_h_imgs[index] = int(out_height)

            encoders.append(encoder)
            encoder.start()
            # Trigger the decoder and video frame anonymization
            decoder = AMQP2VIDEO(event.message.properties['sourceId'], event.message.properties['dataSampleRate'], event.message.properties['locationQuadkey'])
            decoders.append(decoder)
            decoder.start()
            while decoder.playing == False:
                time.sleep(1.0/float(event.message.properties['dataSampleRate']))

        gst_buffer = Gst.Buffer.new_allocate(None, int(event.message.properties['body_size']), None) 
        gst_buffer.fill(0, event.message.body)

        # set pts and duration to be able to record video, calculate fps
        gst_buffer.pts = dec_ptss[index]
        dec_ptss[index] = dec_ptss[index] + dec_durations[index]  # Increase pts by duration
        gst_buffer.duration = dec_durations[index]

        # emit <push-buffer> event with Gst.Buffer
        decoder.appsrc.emit("push-buffer", gst_buffer)

        self._messages_actually_received += 1
        #event.connection.close()
        #self._stopping = True

    def on_transport_error(self, event):
        raise Exception(event.transport.condition)


if __name__ == "__main__":
    try:
        # initialize GStreamer
        Gst.init(sys.argv[1:])
        Container(Receiver(address.url)).run()
    except KeyboardInterrupt:
        pass
