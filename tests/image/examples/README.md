# Examples

This document guides the integration purposes include a readme with scenario and pre-conditions, and scripts/Dockers

## Scenario

A image sensor wants to push several images that have to be anonymised by the MEC platform

## Pre-Conditions

The following systems must be configured and running:

- The Message Broker (AMQP) is running and ready in the MEC infrastructure which has been previously registered in the Discovery at the Cloud EKS
- The Kakfa Broker (KAFKA) is running and ready at Cloud EKS and pulling data through Kafka Connector and KSQLDB from AMQP
- The Image Anonymizator is running and ready in the MEC infrastructure
- The component for the Image Sensor is built but not running

## Push image through MEC infrastructure

In [https://github.com/5gmetadmin/message-data-broker/tree/main/examples/activemq_clients/image_sender_python](https://github.com/5gmetadmin/message-data-broker/tree/main/examples/activemq_clients/image_sender_python) you can find several examples about sending your images through 5GMETA infrastructure depending if you are using S&D database or not.

In this example we will focus in an example that does NOT uses S&D database. We were using sender.py example. This example will push sample_image1.jpg into AMQP from MEC.

```
$ pip3 install -r requirements.txt
```

```
$ python3 sender.py
```

## Read image from EKS infrastructure

* Run client.py ([https://github.com/5gmetadmin/stream-data-gateway/blob/main/utils/platform-client/client.py](https://github.com/5gmetadmin/stream-data-gateway/blob/main/utils/platform-client/client.py)) in order to get appropriate topic and Stream Data Gateway address and port.
* Create output folder to store received images
* Run image-consumer.py from [https://github.com/5gmetadmin/stream-data-gateway/blob/main/examples/consumer/image/image-consumer.py](https://github.com/5gmetadmin/stream-data-gateway/blob/main/examples/consumer/image/image-consumer.py)

