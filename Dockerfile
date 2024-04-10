FROM fluxrm/flux-sched:focal

# Based off of https://github.com/jupyterhub/zero-to-jupyterhub-k8s/tree/main/images/singleuser-sample
# Local usage
# docker run -p 8888:8888 -v $(pwd):/home/jovyan/work test

USER root

ENV NB_USER=jovyan \
    NB_UID=1000 \
    HOME=/home/jovyan \
    VENV_DIR=/home/jovyan/.flux_tutorial_venv

RUN adduser \
    --disabled-password \
    --gecos "Default user" \
    --uid ${NB_UID} \
    --home ${HOME} \
    --force-badname \
    ${NB_USER}

RUN apt-get update \
    # && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    gcc-10 \
    g++-10 \
    ca-certificates \
    dnsutils \
    iputils-ping \
    python3.9 \
    python3.9-dev \
    python3-pip \
    python3-venv \
    openmpi-bin \
    openmpi-common \
    libopenmpi-dev \
    liblz4-dev \
    tini \
    # requirement for nbgitpuller
    git \
    && rm -rf /var/lib/apt/lists/*

ENV CC=gcc-10 \
    CXX=g++-10

RUN pip install git+https://github.com/argonne-lcf/dlio_benchmark.git

RUN pip install dlio-profiler-py
ENV DLIO_PROFILER_ENABLE=0
# RUN dlio_benchmark workload=unet3d_a100 ++workload.dataset.data_folder=/root/data ++workload.workflow.generate_data=True ++workload.workflow.train=False ++workload.dataset.record_length=4096 ++workload.dataset.record_length_stdev=0 ++workload.dataset.record_length_resize=0 ++workload.reader.batch_size=1 ++workload.dataset.num_files_train=16 ++workload.reader.read_threads=1

# RUN dlio_benchmark workload=unet3d_a100 ++workload.dataset.data_folder=/root/data ++workload.workflow.generate_data=False ++workload.workflow.train=True ++workload.dataset.record_length=4096 ++workload.dataset.record_length_stdev=0 ++workload.dataset.record_length_resize=0 ++workload.reader.batch_size=1 ++workload.dataset.num_files_train=16 ++workload.reader.read_threads=1]

ENTRYPOINT [ "/bin/bash" ]