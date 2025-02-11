# Image anonymisation

## Introduction

This repository provides the modules to anonymise image streams at the MEC infrastructures.
Accepted image formats are:
  * JPG

## Prerequisites

The prerequisites here are:
- Infrastructure:
	- A Kubernetes infrastructure for the 5GMETA MEC platform already registered at the 5GMETA Cloud Discovery service
	- To have access to the 5GMETA Cloud platform Discovery service
	- To have a AMQP server running at the discovered 5GMETA MEC platform
- Device:
	- Have a virtualized NVIDIA GPU operated through K8s

## Deployment

The instructions for that can be found in `deploy` folder while the code in `src` folder

go to src/

```
$ docker build -t image-pet .
```

run docker with environment variables AMQP_IP=YOUR_LOCAL_IP :

```
docker run -e AMQP_USER=5gmeta-user -e AMQP_PASS=5gmeta-password -e  AMQP_IP=amqp-ip -e AMQP_PORT=5673 -e TOPIC_READ=image -e TOPIC_WRITE=image_anonym -e INSTANCE_TYPE=small -ti image-pet
```

## Credits

* Josu Pérez ([jperez@vicomtech.org](jperez@vicomtech.org)


## Conclusions and Perspectives



## References



## License

Copyright : Copyright 2022 VICOMTECH

License : EUPL 1.2 ([https://eupl.eu/1.2/en/](https://eupl.eu/1.2/en/))

The European Union Public Licence (EUPL) is a copyleft free/open source software license created on the initiative of and approved by the European Commission in 23 official languages of the European Union.

Licensed under the EUPL License, Version 1.2 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at [https://eupl.eu/1.2/en/](https://eupl.eu/1.2/en/)

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
