#!/bin/bash

set -euo pipefail

################################################################
#
# Flux, Usernetes, Jupyter, and EFA
# I started with ubuntu 24.04 ARM server edition

sudo apt-get update && sudo apt-get install -y build-essential \
    tar \
    autoconf \
    automake \
    make \
    wget \
    git \
    gcc \
    g++ \
    zip \
    libblas-dev \
    liblapack-dev \
    libfftw3-dev libfftw3-bin \
    libxml2-16 libxml2-dev \
    hdf5-tools \
    libhdf5-dev \
    cmake \
    libboost-all-dev \
    && sudo apt-get clean

# Utilities
sudo apt-get update && \
    sudo apt-get -qq install -y --no-install-recommends \
        apt-utils \
        locales \
        ca-certificates \
        wget \
        man \
        git \
        flex \
        ssh \
        sudo \
        vim \
        luarocks \
        munge \
        lcov \
        ccache \
        lua5.4 \
        python3-dev \
        python3-pip \
        valgrind \
        jq && \
    sudo rm -rf /var/lib/apt/lists/*

# Compilers, autotools
sudo apt-get update && \
    sudo apt-get -qq install -y --no-install-recommends \
        build-essential \
        pkg-config \
        autotools-dev \
        libtool \
	libffi-dev \
        autoconf \
        automake \
        make \
        clang \
        clang-tidy \
        gcc \
        g++ && \
    sudo rm -rf /var/lib/apt/lists/*

sudo pip install --upgrade --ignore-installed --break-system-packages \
        "markupsafe==2.0.0" \
        coverage cffi ply six pyyaml "jsonschema>=2.6,<4.0" \
        sphinx sphinx-rtd-theme sphinxcontrib-spelling 
   
sudo apt-get update && \
    sudo apt-get -qq install -y --no-install-recommends \
        libsodium-dev \
        libzmq3-dev \
        certbot \
        nginx \
        libczmq-dev \
        libjansson-dev \
        libmunge-dev \
        libncursesw5-dev \
        liblua5.2-dev \
        liblz4-dev \
        libsqlite3-dev \
        uuid-dev \
        libhwloc-dev \
        libs3-dev \
        libevent-dev \
        libarchive-dev \
        libpam-dev && \
    sudo rm -rf /var/lib/apt/lists/*

# Testing utils and libs
sudo apt-get update && \
    sudo apt-get -qq install -y --no-install-recommends \
        faketime \
        libfaketime \
        pylint \
        cppcheck \
        enchant-2 \
        aspell \
        aspell-en && \
    sudo rm -rf /var/lib/apt/lists/*

sudo locale-gen en_US.UTF-8

# NOTE: luaposix installed by rocks due to Ubuntu bug: #1752082 https://bugs.launchpad.net/ubuntu/+source/lua-posix/+bug/1752082
sudo luarocks install luaposix

# Install openpmix, prrte. Openpmix (pmix2) seems to be installed by hwloc, v5.x
sudo mkdir -p /opt/flux
sudo chown -R ubuntu /opt/flux
cd /opt/flux
git clone --recurse-submodules https://github.com/openpmix/prrte.git && \
    cd prrte && \
    git checkout v3.0.1 && \
    ./autogen.pl && \
    ./configure --prefix=/opt/prrte && \
    make -j && sudo make -j all install
 
export LANG=C.UTF-8
export FLUX_SECURITY_VERSION=0.15.0

cd /opt/flux
CCACHE_DISABLE=1 && \
    V=$FLUX_SECURITY_VERSION && \
    PKG=flux-security-$V && \
    URL=https://github.com/flux-framework/flux-security/releases/download && \
    wget ${URL}/v${V}/${PKG}.tar.gz && \
    tar xvfz ${PKG}.tar.gz && \
    cd ${PKG} && \
    ./configure --prefix=/usr --sysconfdir=/etc || cat config.log && \
    make -j 4 && \
    sudo make install && \
    cd .. && \
    rm -rf flux-security-*

# Setup MUNGE directories & key
sudo mkdir -p /var/run/munge && \
    dd if=/dev/urandom bs=1 count=1024 > munge.key && sudo mv munge.key /etc/munge/munge.key && \
    sudo chown -R munge /etc/munge/munge.key /var/run/munge && \
    sudo chmod 600 /etc/munge/munge.key

cd /opt/flux
export FLUX_CORE_VERSION=0.86.0
wget https://github.com/flux-framework/flux-core/releases/download/v${FLUX_CORE_VERSION}/flux-core-${FLUX_CORE_VERSION}.tar.gz && \
    tar xzvf flux-core-${FLUX_CORE_VERSION}.tar.gz && \
    cd flux-core-${FLUX_CORE_VERSION} && \
    ./configure --prefix=/usr --sysconfdir=/etc && \
    make clean && \
    make -j && \
    sudo make install

sudo apt-get update
sudo apt-get -qq install -y --no-install-recommends \
	libboost-graph-dev \
	libboost-system-dev \
	libboost-filesystem-dev \
	libboost-regex-dev \
	libyaml-cpp-dev \
	libedit-dev \
        libboost-dev \
        libyaml-cpp-dev \
	curl

export FLUX_SCHED_VERSION=0.52.0
cd /opt/flux
wget https://github.com/flux-framework/flux-sched/releases/download/v${FLUX_SCHED_VERSION}/flux-sched-${FLUX_SCHED_VERSION}.tar.gz && \
    tar -xzvf flux-sched-${FLUX_SCHED_VERSION}.tar.gz && \
    cd flux-sched-${FLUX_SCHED_VERSION} && \
    ./configure --prefix=/usr --sysconfdir=/etc && \
    make -j && \
    sudo make install && \
    sudo ldconfig

sudo apt-get update && \
    sudo apt-get install -y libfftw3-dev libfftw3-bin pdsh libfabric-dev libfabric1 \
        openssh-client openssh-server \
        dnsutils telnet strace git g++ \
        unzip bzip2

# Additional debugging
sudo apt-get update && \
    sudo apt-get install -y pdsh \
        openssh-client openssh-server \
        dnsutils telnet strace \
        unzip bzip2

# Install oras for saving artifacts
export VERSION="1.2.0" && \
    curl -LO "https://github.com/oras-project/oras/releases/download/v${VERSION}/oras_${VERSION}_linux_arm64.tar.gz" && \
    mkdir -p oras-install/ && \
    tar -zxf oras_${VERSION}_*.tar.gz -C oras-install/ && \
    sudo mv oras-install/oras /usr/local/bin/ && \
    rm -rf oras_${VERSION}_*.tar.gz oras-install/
    
# Additional packages
sudo apt-get update && sudo apt-get install -y ibverbs-utils libibverbs-dev libibverbs1 && sudo apt-get clean

sudo curl -O https://efa-installer.amazonaws.com/aws-efa-installer-1.42.0.tar.gz && \
    tar -xzvf aws-efa-installer-1.42.0.tar.gz && \
    rm -rf aws-efa-installer-1.42.0.tar.gz && \
    cd aws-efa-installer && \
    sudo ./efa_installer.sh --skip-kmod --yes

export PATH=/opt/amazon/openmpi/bin/:$PATH
cd /opt/
sudo git clone https://github.com/lammps/lammps.git && \
    sudo chown -R ubuntu /opt/lammps && \
    cd /opt/lammps && \
    git fetch --depth 1 origin a8687b53724b630fb5f454c8d7be9f9370f8bb3b && \
    git checkout FETCH_HEAD && \
    mkdir build && \
    cd build && \
    cmake ../cmake -D PKG_REAXFF=yes -D BUILD_MPI=yes -D PKG_OPT=yes -D FFT=FFTW3 -D  MPI_CXX_COMPILER=mpicxx \
    -D CMAKE_INSTALL_PREFIX=/usr \
    && make && sudo make install 

# Flux curve.cert
# Ensure we have a shared curve certificate
flux keygen /tmp/curve.cert && \
    sudo mkdir -p /etc/flux/system && \
    sudo cp /tmp/curve.cert /etc/flux/system/curve.cert && \
    sudo chown ubuntu /etc/flux/system/curve.cert && \
    sudo chmod o-r /etc/flux/system/curve.cert && \
    sudo chmod g-r /etc/flux/system/curve.cert && \
    # Permissions for imp
    sudo chmod u+s /usr/libexec/flux/flux-imp && \
    sudo chmod 4755 /usr/libexec/flux/flux-imp && \
    # /var/lib/flux needs to be owned by the instance owner
    sudo mkdir -p /var/lib/flux && \
    sudo chown ubuntu -R /var/lib/flux

# Install Usernetes
cd /opt
echo "START updating cgroups2"
cat /etc/default/grub | grep GRUB_CMDLINE_LINUX=
GRUB_CMDLINE_LINUX=""
sudo sed -i -e 's/^GRUB_CMDLINE_LINUX=""/GRUB_CMDLINE_LINUX="systemd.unified_cgroup_hierarchy=1"/' /etc/default/grub
sudo update-grub
sudo mkdir -p /etc/systemd/system/user@.service.d

cd /opt/lammps
cat <<EOF | tee delegate.conf
[Service]
Delegate=cpu cpuset io memory pids
EOF
sudo mv ./delegate.conf /etc/systemd/system/user@.service.d/delegate.conf

sudo systemctl daemon-reload
echo "DONE updating cgroups2"

echo "START updating kernel modules"
sudo modprobe ip_tables
tee ./usernetes.conf <<EOF >/dev/null
br_netfilter
vxlan
EOF

sudo mv ./usernetes.conf /etc/modules-load.d/usernetes.conf
sudo systemctl restart systemd-modules-load.service
echo "DONE updating kernel modules"

echo "START 99-usernetes.conf"
echo "net.ipv4.conf.default.rp_filter = 2" > /tmp/99-usernetes.conf
sudo mv /tmp/99-usernetes.conf /etc/sysctl.d/99-usernetes.conf
sudo sysctl --system
echo "DONE 99-usernetes.conf"

echo "START modprobe"
sudo modprobe vxlan
sudo systemctl daemon-reload

# https://github.com/rootless-containers/rootlesskit/blob/master/docs/port.md#exposing-privileged-ports
cp /etc/sysctl.conf ./sysctl.conf
echo "net.ipv4.ip_unprivileged_port_start=0" | tee -a ./sysctl.conf
echo "net.ipv4.conf.default.rp_filter=2" | tee -a ./sysctl.conf
sudo mv ./sysctl.conf /etc/sysctl.conf

sudo sysctl -p
sudo systemctl daemon-reload
echo "DONE modprobe"

echo "START kubectl"
cd /tmp
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/arm64/kubectl"
chmod +x ./kubectl
sudo mv ./kubectl /usr/bin/kubectl
echo "DONE kubectl"

echo "Installing docker"
curl -o install.sh -fsSL https://get.docker.com
chmod +x install.sh
sudo ./install.sh
echo "done installing docker"

# https://github.com/docker/docs/issues/14491
sudo apt install -y systemd-container

sudo chown -R ubuntu /home/ubuntu
echo "Setting up usernetes"
echo "export PATH=/usr/bin:$PATH" >> ~/.bashrc
echo "export XDG_RUNTIME_DIR=/home/ubuntu/.docker/run" >> ~/.bashrc
# This wants to write into run, which is probably OK (under userid)
echo "export DOCKER_HOST=unix:///home/ubuntu/.docker/run/docker.sock" >> ~/.bashrc

echo "Installing docker user"
sudo loginctl enable-linger ubuntu
ls /var/lib/systemd/linger
mkdir -p /home/ubuntu/.docker/run

# This might show failure because it creates the docker.sock in /run/user/UID/docker.sock
# but then we link to the expected path below
sudo apt-get install -y uidmap
dockerd-rootless-setuptool.sh install
sleep 10
systemctl --user enable docker.service
systemctl --user start docker.service

# Not sure why this is happening, but it's starting here
# As long as docker run hello world works we are good!
ln -s /run/user/1000/docker.sock /home/ubuntu/.docker/run/docker.sock
docker run hello-world

sudo sysctl -w net.ipv4.ip_unprivileged_port_start=0
sysctl net.ipv4.ip_unprivileged_port_start   # confirm it reads 0

# Write scripts to start control plane and worker nodes
# Clone usernetes and usernetes-python
git clone https://github.com/rootless-containers/usernetes ~/usernetes

echo "Done installing docker user"
sudo chown ubuntu /etc/flux/system/curve.cert
sudo chown -R ubuntu /home/ubuntu

# Additional requirements for Jupyter
export NB_USER=ubuntu
export NB_UID=1000

sudo apt-get install -y dnsutils \
    iputils-ping \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    tini

sudo apt-get install -y python3-greenlet
pip3 install ruamel.yaml.clib --break-system-packages
wget https://gist.githubusercontent.com/vsoch/2b66b6f2b3885fc9c747e38cc73b78e2/raw/7d596101d87e20e55b5cac589acadb232b29ed3c/requirements.txt
sudo python3 -m pip install -r requirements.txt --break-system-packages
sudo python3 -m pip install ipykernel --break-system-packages
sudo python3 -m pip install pycurl --break-system-packages
sudo python3 -m pip install ipython --break-system-packages && sudo python3 -m IPython kernel install 

# Flux accounting
git clone https://github.com/flux-framework/flux-accounting && \
    cd flux-accounting && \
    ./autogen.sh && \
    ./configure --prefix=/usr && \
    make -j && sudo make install

# This is for arm
wget https://nodejs.org/dist/v20.15.0/node-v20.15.0-linux-arm64.tar.xz && \
    sudo apt-get update && sudo apt-get install -y xz-utils && sudo rm -rf /var/lib/apt/lists/* && \
    xz -d -v node-v20.15.0-linux-arm64.tar.xz && \
    sudo tar -C /usr/local --strip-components=1 -xvf node-v20.15.0-linux-arm64.tar

# sudo apt-get purge -y nodejs npm
# sudo apt-get autoremove -y
# curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
# sudo apt-get install -y nodejs
# sudo rm -rf /usr/local/bin/node

# This customizes the launcher UI
# https://jupyter-app-launcher.readthedocs.io/en/latest/usage.html
sudo python3 -m pip install jupyter_app_launcher --break-system-packages && \
sudo python3 -m pip install --upgrade jupyter-server --break-system-packages && \
sudo python3 -m pip install jupyter-launcher-shortcuts --break-system-packages && \
sudo python3 -m pip install jupyterhub_idle_culler --break-system-packages
sudo mkdir -p /usr/local/share/jupyter/lab/jupyter_app_launcher
python3 -m pip install jupyterhub boto3 --break-system-packages
python3 -m pip install git+https://github.com/kubeflow/sdk.git@main#subdirectory=python --break-system-packages
sudo python3 -m pip install river riverapi --break-system-packages
sudo python3 -m pip install ipywidgets --break-system-packages

# For Chapter 5: hybrid quantum-classical QAOA on AWS Braket SV1
sudo python3 -m pip install amazon-braket-sdk scipy --break-system-packages

sudo apt-get install -y bash-completion

# This is for riverML
sudo python3 -m pip install river riverapi --break-system-packages

# COPY ./tutorial /home/jovyan/
# COPY ./docker/jupyter-launcher.yaml /usr/local/share/jupyter/lab/jupyter_app_launcher/jp_app_launcher.yaml
# ENV JUPYTER_APP_LAUNCHER_PATH=/usr/local/share/jupyter/lab/jupyter_app_launcher/
# Give jovyan user permissions to tutorial materials
# RUN chmod -R 777 ~/ /home/jovyan
# COPY ./docker/flux-icon.png $HOME/flux-icon.png
# note that previous examples are added via git volume in config.yaml
# ENV SHELL=/usr/bin/bash
# ENV FLUX_URI_RESOLVE_LOCAL=t
# This is for JupyterHub
# COPY ./docker/entrypoint.sh /entrypoint.sh
# This is for a local start
# COPY ./docker/start.sh /start.sh
mkdir -p $HOME/.local/share && \
chmod 777 $HOME/.local/share

# Quick setup of flux-accounting (not working due to needing system service)
# RUN flux start /bin/bash -c "nohup flux account create-db && flux account-service & flux account add-bank root 1" && \
#    flux start flux account add-bank --parent-bank=root default 1 && \
#    flux start flux account add-user --username=jovyan --bank=default && \
#    flux start flux jobtap load mf_priority.so && \
#    flux start flux account-update-db

# sudo rm /usr/local/bin/node
sudo npm install -g configurable-http-proxy
# CMD ["flux", "start", "--test-size=4", "jupyter", "lab"]
# 
# Build usernetes image
cd /home/ubuntu/usernetes
docker build -t usernetes_node .
# At this point we have what we need!
