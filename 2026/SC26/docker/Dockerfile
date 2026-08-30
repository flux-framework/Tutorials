# Flux tutorial image for SC26.
#
# Build from the 2026/SC26 directory:
#   docker build -f ./docker/Dockerfile -t ghcr.io/flux-framework/flux-tutorial:sc26 .
#
# Run locally:
#   docker run --rm -it -p 8888:8888 ghcr.io/flux-framework/flux-tutorial:sc26
#
# Adapted from 2026/HPSF/docker/Dockerfile. Changes for SC26:
#   - copies the module1/module2/module3 tree instead of ch1..ch5
#   - adds qiskit, qiskit-aer, and scipy for the Module 2 quantum notebook
#   - drops amazon-braket-sdk (that example was replaced by a local simulator)
#   - drops flux-mcp (the agentic section was cut)
FROM fluxrm/flux-sched:noble

USER root

ENV NB_USER=jovyan \
    NB_UID=1000 \
    HOME=/home/jovyan

RUN adduser \
    --disabled-password \
    --gecos "Default user" \
    --uid ${NB_UID} \
    --home ${HOME} \
    --force-badname \
    ${NB_USER}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    gcc-10 \
    g++-10 \
    ca-certificates \
    dnsutils \
    iputils-ping \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    openmpi-bin \
    openmpi-common \
    libopenmpi-dev \
    liblz4-dev \
    tini \
    nodejs \
    python3-greenlet \
    jq \
    # requirement for nbgitpuller
    git \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY ./docker/requirements_venv.txt ./requirements_venv.txt
RUN python3 -m venv $VIRTUAL_ENV && pip install --no-cache-dir -r requirements_venv.txt
COPY ./docker/requirements.txt ./requirements.txt

RUN pip install ruamel.yaml.clib && \
    pip install -r requirements.txt && \
    pip install ipykernel pycurl IPython && \
    python -m IPython kernel install

# Module 2: hybrid quantum-classical QAOA on a local simulator.
# No cloud account or credentials are needed.
COPY ./tutorial/module2/scripts/requirements.txt ./requirements_quantum.txt
RUN pip install --no-cache-dir -r requirements_quantum.txt

RUN wget https://nodejs.org/dist/v20.15.0/node-v20.15.0-linux-x64.tar.xz && \
    apt-get update && apt-get install -y xz-utils && rm -rf /var/lib/apt/lists/* && \
    xz -d -v node-v20.15.0-linux-x64.tar.xz && \
    tar -C /usr/local --strip-components=1 -xvf node-v20.15.0-linux-x64.tar

# This customizes the launcher UI
# https://jupyter-app-launcher.readthedocs.io/en/latest/usage.html
RUN pip install jupyter_app_launcher && \
    pip install --upgrade jupyter-server && \
    pip install jupyter-launcher-shortcuts && \
    pip install jupyterhub_idle_culler && \
    mkdir -p /usr/local/share/jupyter/lab/jupyter_app_launcher && \
    pip install jupyterhub && \
    pip install ipywidgets

COPY ./tutorial /home/jovyan/
COPY ./docker/jupyter-launcher.yaml /usr/local/share/jupyter/lab/jupyter_app_launcher/jp_app_launcher.yaml
ENV JUPYTER_APP_LAUNCHER_PATH=/usr/local/share/jupyter/lab/jupyter_app_launcher/

# Give jovyan user permissions to tutorial materials
RUN chmod -R 777 ~/ /home/jovyan

WORKDIR $HOME
COPY ./docker/flux-icon.png $HOME/flux-icon.png

ENV SHELL=/usr/bin/bash
ENV FLUX_URI_RESOLVE_LOCAL=t

EXPOSE 8888
ENTRYPOINT ["tini", "--"]

# This is for JupyterHub
COPY ./docker/entrypoint.sh /entrypoint.sh
RUN mkdir -p $HOME/.local/share && \
    chmod 777 $HOME/.local/share

USER ${NB_USER}

CMD ["flux", "start", "--test-size=4", "jupyter", "lab", "--ip=0.0.0.0"]
