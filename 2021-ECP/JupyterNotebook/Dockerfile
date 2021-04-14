#This is a sample Image 
FROM ubuntu:latest 
MAINTAINER patki1@llnl.gov

ENV TZ="America/Los_Angeles"
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt-get update #&& yes | unminimize  

RUN apt-get -y --no-install-recommends install \
    vim \
    man \
    manpages-dev \
    man-db \
    manpages-posix \
    manpages-posix-dev \
    ubuntu-docs \
    libc6-dev \
    wget \
    systemd \
    firefox \
    git \
    autoconf \
    automake \
    libtool \
    make 

RUN apt-get -y --no-install-recommends install pkg-config \
    libsodium-dev \
    libzmq3-dev \
    libczmq-dev \
    uuid-dev \
    libjansson-dev \
    liblz4-dev \
    libhwloc-dev \
    libsqlite3-dev \
    lua5.1 \
    liblua5.1-dev \
    lua-posix

RUN apt-get -y --no-install-recommends install  python3-dev \
    python3-cffi \
    python3-six \
    python3-yaml \
    python3-jsonschema \
    python3-sphinx \
    python3-pip \
    python3-setuptools \
    aspell \
    aspell-en \
    valgrind \
    libmpich-dev 

RUN \
   echo 'alias python="/usr/bin/python3.6"' >> /root/.bashrc && \
   echo 'alias pip="/usr/bin/pip3"' >> /root/.bashrc && \
   . /root/.bashrc

RUN \
   echo 'set number' >> /root/.vimrc 
 
RUN pip3 install jupyterlab

ENV DISPLAY=host.docker.internal:0

#Fluxion
RUN apt-get -y --no-install-recommends install \
    libhwloc-dev \
    libboost-dev \
    libboost-system-dev \
    libboost-filesystem-dev \
    libboost-graph-dev \
    libboost-regex-dev \
    libxml2-dev \
    libyaml-cpp-dev \ 
    python3-yaml

#Install Flux
RUN cd /root/ && mkdir flux-install
WORKDIR /root/
RUN git clone https://github.com/flux-framework/flux-core.git 
RUN cd /root/flux-core/ && ./autogen.sh && ./configure LDFLAGS="-L/usr/lib/python3.6" --prefix=/root/flux-install --disable-docs && make -j && make install

RUN cd /root/ && git clone https://github.com/flux-framework/flux-sched.git
WORKDIR /root/flux-sched/
ENV PATH "/root/flux-install/bin:$PATH"
ENV PKG_CONFIG_PATH="$PKG_CONFIG_PATH:/flux-framework/flux-install/lib/pkgconfig" 
ENV LD_LIBRARY_PATH "/root/flux-install/lib/flux:/root/flux-install/lib"
RUN ./autogen.sh && ./configure --prefix=/root/flux-install && make -j && make install

RUN cd /root/ && git clone https://github.com/flux-framework/flux-workflow-examples.git
WORKDIR /root/

#Set up the jupyter notebook 
COPY ECPTutorial.ipynb .
COPY sleep_batch.sh .

CMD [“echo”,”Initial Flux Image Created”] 

