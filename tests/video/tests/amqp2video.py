from __future__ import print_function

from proton.handlers import MessagingHandler
from proton.reactor import Container

import os
import sys
import time
import numpy

import gi

gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gst, GObject, GLib, GstApp, GstVideo

import address

pts = 0  # buffers presentation timestamp

# AMQP receiver
class Receiver(MessagingHandler):
    def __init__(self, url):
        super(Receiver, self).__init__()
        self.url = url
        self._messages_actually_received = 0
        self._stopping = False

    def on_start(self, event):
        print("Receiver Created")
        event.container.create_receiver(self.url)

    def on_message(self, event):
        global pts
        global duration

        if self._stopping:
            return

        print(event.message.properties['body_size'])
        print(
            "Received frame Content-Type: video/x-h264 of size {size}".format(size=event.message.properties['body_size']))
        # Discriminate video frames from a single/specific source
        if (event.message.properties['sourceId'] == 55):
            gst_buffer = Gst.Buffer.new_allocate(None, int(event.message.properties['body_size']), None) 
            gst_buffer.fill(0, event.message.body)

            # set pts and duration to be able to record video, calculate fps
            framerate = float(event.message.properties['dataSampleRate'])
            duration = 10**9 / (int(framerate / 1.0))  # frame duration

            pts += duration  # Increase pts by duration
            gst_buffer.pts = pts
            gst_buffer.duration = duration

            # emit <push-buffer> event with Gst.Buffer
            appsrc.emit("push-buffer", gst_buffer)

        self._messages_actually_received += 1
        #event.connection.close()
        #self._stopping = True

    def on_transport_error(self, event):
        raise Exception(event.transport.condition)


if __name__ == "__main__":

    appsrc = None

    pipeline = None
    bus = None
    message = None

    # initialize GStreamer
    Gst.init(sys.argv[1:])

    # build the pipeline to play the video frames
    pipeline = Gst.parse_launch(
        'appsrc caps="video/x-h264, stream-format=byte-stream, alignment=au" name=appsrc ! h264parse config-interval=-1 ! decodebin ! videoconvert ! autovideosink'
    )

    appsrc = pipeline.get_by_name("appsrc")  # get AppSrc
    # instructs appsrc that we will be dealing with timed buffer
    appsrc.set_property("format", Gst.Format.TIME)

    # instructs appsrc to block pushing buffers until ones in queue are preprocessed
    # allows to avoid huge queue internal queue size in appsrc
    appsrc.set_property("block", True)

    # start playing
    print("Pipeline Playing")
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("Unable to set the pipeline to the playing state.")
        exit(-1)


    print("Container RECEIVER")
    Container(Receiver(address.url)).run()

    # wait until EOS or error
    bus = pipeline.get_bus()

    # free resources
    pipeline.set_state(Gst.State.NULL)
