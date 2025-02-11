# Testing video-anonymizator locally

This repository will guide the testing of the video anonymizator for H.264 video data

## Overview
This folder provides the guidelines to test functionality, performance and concurrency of the solution.

The different steps in terms of testing to accomplish are:

 1. Built the Docker of anonymization
 2. Run the AMQP message-broker to deliver signalling messages
 3. Run the video-stream-broker to push the video from the Sensor and Device to the **`video`** _topic_
 4. Push Video stream(s) to the video-stream-broker
 5. Consume the Video Stream from the **`video_anonym`** _topic_ from the message-broker


## Deployment

### Follow the steps for basic test

1. run the message-broker docker:

```
sudo docker-compose up -d
```

2. run the video-stream-broker docker with environment variables:

```
docker run  --net=host --env AMQP_USER="<user>" --env AMQP_PASS="<password>" --env AMQP_IP="<AAA.BBB.CCC.DDD>" --env AMQP_PORT="<port>" 5gmeta/webrtc_proxy
```

_Remember to set the `<user`>, `<password`>, `<AAA.BBB.CCC.DDD`> and `<port`> to your local environment_

> _AAA.BBB.CCC.DDD_ is the IP address of the AMQP message_broker

3. build the video-anonymizator docker from the `Dockerfile`:

```
docker build -t 5gmeta/video-anonymizator .
```

4. run the video-anonymizator docker with environment variables:

```
docker run  --net=host --env AMQP_USER="<user>" --env AMQP_PASS="<password>" --env AMQP_IP="<AAA.BBB.CCC.DDD>" --env AMQP_PORT="<port>" --env TOPIC_READ="video" --env TOPIC_WRITE="video_anonym" --env INSTANCE_TYPE="small" 5gmeta/video-anonymizator
```

_Remember to set the `<user`>, `<password`>, `<AAA.BBB.CCC.DDD`> and `<port`> to your local environment_

> _192.168.1.101_ is the IP address of the AMQP message_broker

5. modify the video-sensor docker to avoid using the Cloud systems (Discovery, Registration, ...):

 - a) Setup FPS of the video source to be used in the metadata @ video_sensor.py

```
"dataSampleRate": 2.0,
```

 - b) Setup local environment @ video_sensor.py

```
    # # Get Message Broker access
    # service="message-broker"
    # messageBroker_ip, messageBroker_port = discovery_registration.discover_sb_service(tile18,service)
    # if messageBroker_ip == -1 or messageBroker_port == -1:
    #     print(service+" service not found")
    #     exit(-1)
     
    # # Register a New stream into the System
    # service="registration-api"
    # Registration_ip, Registration_port = discovery_registration.discover_sb_service(tile18,service)
    # if Registration_ip == -1 or Registration_port == -1:
    #     print(service+" service not found")
    #     exit(-1)
 
    # # Get Video Broker access
    # service="video-broker"
    # videoBroker_ip, videoBroker_port = discovery_registration.discover_sb_service(tile18,service)
    # if videoBroker_ip == -1 or videoBroker_port == -1:
    #     print(service+" service not found")
    #     exit(-1)
 
    # # Get Topic and dataFlowId to push data into the Message Broker
    # dataflowId, topic = discovery_registration.register(dataflowmetadata, tile18)
 
    print("\n\tREGISTRATION DONE\n")
 
    # To be Removed - Local Test
    messageBroker_ip = '127.0.0.1'
    messageBroker_port = '5673'
    videoBroker_ip = 'localhost'
    videoBroker_port = 8443
    dataflowId = 54 # Force/Set the ID which is provided by the Registration
    topic = 'video'
```

6. produce a video sensor source

```
gst-launch-1.0 filesrc location="/5GMETA/video-anonymizator/processor/res/testimg/input/RecFile_2_20220405_095958_EthCamMJPEG_1_oImageLeft_0.jpg" ! decodebin ! imagefreeze ! video/x-raw, framerate=1/1 ! videoconvert ! videoscale ! video/x-raw, width=320, height=240, framerate=2/1 ! textoverlay font-desc="Arial 40px" text="container TX" valignment=2 ! timeoverlay font-desc="Arial 60px" valignment=2 ! videoconvert ! tee name=t ! queue max-size-buffers=1 ! x264enc bitrate=2000 speed-preset=ultrafast tune=zerolatency key-int-max=5 ! video/x-h264,profile=constrained-baseline,stream-format=byte-stream ! h264parse config-interval=-1 ! rtph264pay pt=96 config-interval=-1 name=payloader ! application/x-rtp,media=video,encoding-name=H264,payload=96 ! udpsink host=127.0.0.1 port=7000 enable-last-sample=false send-duplicates=false
```

> use an image path already in the repository such as `"video-anonymizator/processor/res/testimg/input/RecFile_2_20220405_095958_EthCamMJPEG_1_oImageLeft_0.jpg"` \
> framerate=2/1 is set accordingly to the `"dataSampleRate": 2.0,` defined @ video_sensor.py \
> source in the free PORT 7000

7. build the video-sensor docker

```
docker build -t 5gmeta/video_sensor video_sensor/.
```

8. run the video-sensor docker with environment variables:

```
docker run  --net=host --env VIDEO_SOURCE="udp" --env VIDEO_PARAM="7000" --env VIDEO_TTL="300" 5gmeta/video_sensor
```

> source in PORT 7000 \
> after 300 secs video sensor will stop

9. playback anonymised video

```
AMQP_USER="<user>" AMQP_PASS="<password>" AMQP_IP="<AAA.BBB.CCC.DDD>" AMQP_PORT="<port>" GST_DEBUG=3 python3 ./amqp2video.py
```

_Remember to set the `<user`>, `<password`>, `<AAA.BBB.CCC.DDD`> and `<port`> to your local environment_

### Follow the steps for GPU accelerated test:

4. alternatively, run docker with environment variables _when a NVIDIA graphics card is enabled and ready to use_:

```
docker run --gpus all --net=host --env AMQP_USER="<user>" --env AMQP_PASS="<password>" --env AMQP_IP="<AAA.BBB.CCC.DDD>" --env AMQP_PORT="<port>" --env TOPIC_READ="video" --env TOPIC_WRITE="video_anonym" --env INSTANCE_TYPE="advanced" --env ENABLE_NV="True" 5gmeta/video-anonymizator
```

_Remember to set the `<user`>, `<password`>, `<AAA.BBB.CCC.DDD`> and `<port`> to your local environment_

### Follow the steps for concurrency tests:


5. modify the video-sensor docker to avoid using the Cloud systems (Discovery, Registration, ...):

 - Setup another ID @ video_sensor.py

```
dataflowId = 54 # Force/Set the ID which is provided by the Registration process of the Sensor Producer
```

9. playback anonymised video

 - Filter the preffered ID @ amqp2video.py
 
```
if (event.message.properties['sourceId'] == 54):
```

 - Run the playback
 
```
AMQP_USER="<user>" AMQP_PASS="<password>" AMQP_IP="<AAA.BBB.CCC.DDD>" AMQP_PORT="<port>" GST_DEBUG=3 python3 ./amqp2video.py
```

_Remember to set the `<user`>, `<password`>, `<AAA.BBB.CCC.DDD`> and `<port`> to your local environment_

### Follow the steps for low performance test:

4. alternatively, run docker with environment variables to produce low quality resolutions:

```
docker run  --net=host --env AMQP_USER="<user>" --env AMQP_PASS="<password>" --env AMQP_IP="<AAA.BBB.CCC.DDD>" --env AMQP_PORT="<port>" --env TOPIC_READ="video" --env TOPIC_WRITE="video_anonym" --env INSTANCE_TYPE="small" 5gmeta/video-anonymizator
```

_Remember to set the `<user`>, `<password`>, `<AAA.BBB.CCC.DDD`> and `<port`> to your local environment_
