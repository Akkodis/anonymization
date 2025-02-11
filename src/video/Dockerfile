FROM ubuntu:20.04
ENV	NVIDIA_DRIVER_CAPABILITIES compute,utility,video
# Disable Prompt During Packages Installation
ARG DEBIAN_FRONTEND=noninteractive


RUN apt-get update -y
RUN apt-get install python3 python3-pip -y
#RUN apt-get install libprotobuf10 protobuf-compiler libprotoc10 -y
#RUN apt-get install ffmpeg libsm6 libxext6  -y

RUN pip3 install -Iv meson==0.53.2
RUN apt install -y ninja-build


RUN apt update
RUN apt install -y libsoup2.4-1
RUN apt install -y libsoup2.4-dev
RUN apt install -y flex
RUN apt install -y bison

RUN apt update
RUN apt install -y libpango-1.0-0
RUN apt install -y libpango1.0-dev
RUN apt install -y libpango-1.0-0
RUN apt install -y libpango1.0-dev
RUN apt install -y libpangocairo-1.0-0
RUN apt install -y libjson-glib-1.0-0
RUN apt install -y libjson-glib-dev

RUN apt update
RUN apt install -y libavfilter7
RUN apt install -y libavfilter-dev
RUN apt install -y libavformat58
RUN apt install -y libavformat-dev
RUN apt install -y libavresample4
RUN apt install -y libavresample-dev
RUN apt install -y libavcodec58
RUN apt install -y libavcodec-dev
RUN apt install -y libavutil56
RUN apt install -y libavutil-dev

RUN apt install -y libtool
RUN apt install -y git

RUN update-ca-certificates
RUN git config --global http.sslverify false

RUN git clone --branch 1.18 https://github.com/GStreamer/gst-build.git
WORKDIR gst-build
RUN mkdir build
RUN meson --prefix=/usr -Dgpl=enabled -Dgst-plugins-bad:nvcodec=enabled build
#RUN meson --prefix=/usr build
RUN ninja -C build
RUN meson install -C build

RUN apt-get -y --no-install-recommends install \
    python3-gst-1.0 \
    libgirepository1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libcairo2-dev \
    gir1.2-gstreamer-1.0 \
    python3-gi \
    python-gi-dev

RUN apt install -y libjson-glib-1.0-0 libjson-glib-dev

WORKDIR /opt/
COPY ./processor ./processor
WORKDIR /opt/processor/app/weight/
RUN cat weights_face_v1.0.0.pb.a? > weights_face_v1.0.0.pb
RUN cat weights_plate_v1.0.0.pb.a? > weights_plate_v1.0.0.pb

WORKDIR /opt/
COPY requirements.txt ./

RUN pip3 install --upgrade pip
RUN pip3 install object_detection

RUN pip3 install --no-cache-dir -r requirements.txt

RUN pip3 install opencv-python
RUN pip3 install python-qpid-proton
RUN pip3 install tensorflow-addons
RUN pip3 install tensorflow-datasets
RUN pip3 install tensorflow-estimator
RUN pip3 install tensorflow-hub
RUN pip3 install tensorflow-io
RUN pip3 install tensorflow-io-gcs-filesystem
RUN pip3 install tensorflow-metadata
RUN pip3 install tensorflow-model-optimization
RUN pip3 install tensorflow-text
RUN pip3 install tf_slim

WORKDIR /opt/processor

RUN chmod +x ./entrypoint.sh

CMD /opt/processor/entrypoint.sh

