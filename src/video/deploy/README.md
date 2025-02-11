# Deployment

This section overviews the way to deploy the containers for the following modules:
- Video Anonymizator to receive the Video Stream in H.264 in the `video` _topic_ to be processed by Pipelines running at the 5GMETA MEC infrastructure performing anonymisation and pushing resulting frames into the `video_anonym` _topic_. 

The instructions for that can be found in `deployment` folder while the code in `src` folder

## Video Anonymisation

In the `src` folder, a Dockerfile contains all the information related to the container.
The user should build the Dockerfile and then run it with the following steps (modify the `<path>` according to your environment):

To deploy a Docker the instructions are:

    cd <path>/deployment
	docker build -t 5gmeta/video-anonymizator .
	docker run  --net=host --env AMQP_USER="<user>" --env AMQP_PASS="<password>" --env AMQP_IP="<AAA.BBB.CCC.DDD>" --env AMQP_PORT="<port>" --env TOPIC_READ="video" --env TOPIC_WRITE="video_anonym" --env INSTANCE_TYPE="small" 5gmeta/video-anonymizator

_Remember to configure the `<user`>, `<password`>, `<AAA.BBB.CCC.DDD`> and `<port`> to your local environment_

> AMQP_IP and AMQP_PORT vars are required and set to the local configuration of the message broker running in a MEC infraestructure
> INSTANCE_TYPE can be "small" "medium" "large" "advanced"

***To see how to execute it go to the `examples` folder***
