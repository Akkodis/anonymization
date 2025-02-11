FROM ubuntu:20.04
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y
RUN apt-get install python3 python3-pip -y
RUN apt-get install libprotobuf-dev protobuf-compiler libprotoc-dev -y
RUN apt-get install ffmpeg libsm6 libxext6  -y

RUN pip3 install --upgrade pip
RUN pip3 install object_detection
RUN pip3 install python-qpid-proton
RUN pip3 install getmac
RUN pip3 install tensorflow-addons
RUN pip3 install tensorflow-datasets
RUN pip3 install tensorflow-estimator
RUN pip3 install tensorflow-hub
RUN pip3 install tensorflow-io
RUN pip3 install tensorflow-io-gcs-filesystem
RUN pip3 install tensorflow-metadata
RUN pip3 install tensorflow-model-optimization
RUN pip3 install tensorflow-text

COPY ./app /app
WORKDIR /app/weight/
RUN cat weights_face_v1.0.0.pb.a? > weights_face_v1.0.0.pb
RUN cat weights_plate_v1.0.0.pb.a? > weights_plate_v1.0.0.pb

WORKDIR /app

RUN pip3 install -r /app/Anonymization-of-Dashcam-Recordings/python-demo/requirements.txt

#COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

CMD /app/entrypoint.sh

