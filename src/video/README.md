# Video Anonymizator

## Introduction

This repository provides the modules to anonymise video streams at the MEC infrastructures.

This way the Video Anonymizator subscribe to all the H.264 video streams in the `video` _topic_ and push processed/anonymised video flows in the `video_anonym` _topic_.

The accepted video formats to be pushed to the discovered 5GMETA MEC platform are:

 - H.264: AVC standard for video (can be extended to HEVC format)

![Sequence Diagram of exchanged Messages](miscelania/seqdiag.png)

## Prerequisites
The prerequisites here are:
- Infrastructure:
	- A Kubernetes infrastructure for the 5GMETA MEC platform already registered at the 5GMETA Cloud Discovery service
	- To have access to the 5GMETA Cloud platform Discovery service
	- To have a AMQP server running at the discovered 5GMETA MEC platform
	- To have a WebRTC proxy running at the discovered 5GMETA MEC platform
- Device:
	- Have a virtualized NVIDIA GPU operated through K8s
- Dependencies
	- The MEC system can use the provided Docker or to natively include these requirements:

> PIP3 \
> docker == 4.1.0 \
> requests == 2.22.0 \
> pygeotile == 1.0.6 \
> object_detection >= 0.0.3 \
> opencv-python >= 4.6.0.66 \
> tensorflow-addons >= 0.18.0 \
> tensorflow-datasets >= 4.7.0 \
> tensorflow-estimator >= 2.10.0 \
> tensorflow-hub >= 0.12.0 \
> tensorflow-io >= 0.27.0 \
> tensorflow-io-gcs-filesystem \
> tensorflow-metadata >= 1.10.0 \
> tensorflow-model-optimization >= 0.7.3 \
> tensorflow-text >= 2.10.0 \
> tf_slim >= 1.1.0 \
> PACKETS \
> gstreamer >= 1.18.5 \
> gstreamer1.0-rtsp \
> python3 \
> python3-pip \
> libjson-glib-1.0-0 \
> libjson-glib-dev \


## Features

Different advanced features are provided when performing naonymisation processing:

 - GPU acceleration: use the NVIDIA features to encode/decode the video streams, needing an NVIDIA GPU virtualized through K8s. For that a parameter `ENABLE\_NV="True"` can be set in the Docker
 - Quality downgrade: reduce the resolution and framerate of the output anonymised video streams to consume less computing assets and fit into the consumer terms. For that the parameters `OUTPUT\_FPS="0"` `OUTPUT\_WIDTH="0"` `OUTPUT\_HEIGHT="0"` allow to keep nominal resolutions and sampling rates (when 0 is set) or to downsample.

## Deployment

In the `deployment` folder different instructions to operate the involved Docker are described.

This section overviews the way to deploy the containers for the following modules:
- Video Anonymizator to receive the Video Stream in H.264 in the `video` _topic_ to be processed by Pipelines running at the 5GMETA MEC infrastructure performing anonymisation and pushing resulting frames into the `video_anonym` _topic_.

The instructions for that can be found in `deploy` folder while the code in `src` folder

## Examples

This document guides the integration purposes include a readme with scenario and pre-conditions, and scripts/Dockers

### Scenario

A video sensor wants to push a UDP video stream including a RTP video with H264 which has to be anonymised by the MEC platform

### Pre-Conditions

The following systems must be configured and running:

- The Message Broker (AMQP) is running and ready in the MEC infrastructure which has been previously registered in the Discovery at the Cloud EKS
- The Video Stream Broker (WebRTC Proxy) is running and ready in the MEC infrastructure
- The Kakfa Broker (KAFKA) is running and ready at Cloud EKS and pulling data through Kafka Connector and KSQLDB from AMQP
- The Video Anonymizator is running and ready in the MEC infrastructure
- The component for the Video Sensor is built but not running

### Push a UDP Source

First, we need a UDP SOURCE:

	gst-launch-1.0 filesrc location="/5GMETA/video-anonymizator/processor/res/testimg/input/RecFile_2_20220405_095958_EthCamMJPEG_1_oImageLeft_0.jpg" ! decodebin ! imagefreeze ! video/x-raw, framerate=1/1 ! videoconvert ! videoscale ! video/x-raw, width=320, height=240, framerate=2/1 ! textoverlay font-desc="Arial 40px" text="container TX" valignment=2 ! timeoverlay font-desc="Arial 60px" valignment=2 ! videoconvert ! tee name=t ! queue max-size-buffers=1 ! x264enc bitrate=2000 speed-preset=ultrafast tune=zerolatency key-int-max=5 ! video/x-h264,profile=constrained-baseline,stream-format=byte-stream ! h264parse config-interval=-1 ! rtph264pay pt=96 config-interval=-1 name=payloader ! application/x-rtp,media=video,encoding-name=H264,payload=96 ! udpsink host=127.0.0.1 port=7000 enable-last-sample=false send-duplicates=false

> use an image path already in the repository such as `"video-anonymizator/processor/res/testimg/input/RecFile_2_20220405_095958_EthCamMJPEG_1_oImageLeft_0.jpg"` \
> framerate=2/1 is set accordingly to the `"dataSampleRate": 2.0,` defined @ video_sensor.py \
> source in the free PORT 7000

Second, we need to run the Video Sensor Docker:

	docker run  --net=host --env AMQP_USER="<user>" --env AMQP_PASS="<password>" --env VIDEO_SOURCE="udp" --env VIDEO_PARAM="7000" --env VIDEO_TTL="300" 5gmeta/video_sensor

 _Remember to configure the `<user`> and `<password`> to your local environment_

> Remember to update the `video_sensor.py` code of the Docker including the employed framerate `"dataSampleRate": 2.0,` \
> Note that 7000 is the UDP source Port \
> Note that 100 is the timeout until the Video Sensor will stop sending a video stream

Third, we can play the video from the 5GMETA MEC infrastructure, checking data pipeline at the 5GMETA MEC infrastructure is processing and anonymising data, from the Local Consume of the AMQP Source

> Note that 23 is the provided ID (from the registration process)

 - change amqp2video.py code to get the target ID

	if (event.message.properties['sourceId'] == 23):

> Note that 23 should be changed to the dataflow ID identified in the logs coming from registration and WebRTC proxy logs

 - launch the player

	AMQP_USER="<user>" AMQP_PASS="<password>" AMQP_IP="<AAA.BBB.CCC.DDD>" AMQP_PORT="<port>" GST_DEBUG=3 python3 ./amqp2video.py

 _Remember to configure the `<user`>, `<password`>, `<AAA.BBB.CCC.DDD`> and `<port`> to your local environment_

> Note that _AAA.BBB.CCC.DDD_ is the IP address of the AMQP message_broker

## Credits

* Angel Martin ([amartin@vicomtech.org](mailto:amartin@vicomtech.org))


## Conclusions



## References



## License

Copyright : Copyright 2022 VICOMTECH

License : EUPL 1.2 ([https://eupl.eu/1.2/en/](https://eupl.eu/1.2/en/))

The European Union Public Licence (EUPL) is a copyleft free/open source software license created on the initiative of and approved by the European Commission in 23 official languages of the European Union.

Licensed under the EUPL License, Version 1.2 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at [https://eupl.eu/1.2/en/](https://eupl.eu/1.2/en/)

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
