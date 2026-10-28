# The QFw on Flux tutorial, as one self contained container.

# Pinned by digest, so a new push to the noble tag cannot change the build.
ARG FLUX_BASE_IMAGE=fluxrm/flux-core:noble@sha256:f884cea3a65b5f13aabb6a151b57c461c67b099eeca1039ee26944c654b79349
FROM ${FLUX_BASE_IMAGE}

LABEL org.opencontainers.image.source="https://github.com/flux-framework/Tutorials" \
      org.opencontainers.image.title="sc26-openqse" \
      org.opencontainers.image.description="QFw on Flux notebook tutorial (Ubuntu noble)"

USER root
WORKDIR /root
ENV DEBIAN_FRONTEND=noninteractive

RUN set -ex \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       autoconf automake bison bzip2 ca-certificates cmake curl diffutils \
       environment-modules file findutils flex g++ gcc gfortran git gnupg gzip \
       hwloc iproute2 jq less libboost-dev libboost-graph-dev libbz2-dev \
       libcurl4-openssl-dev libedit-dev libevent-dev libexpat1-dev libffi-dev \
       libgdbm-dev libhwloc-dev libjansson-dev liblzma-dev libncurses-dev \
       libopenblas-dev libpmix-dev libreadline-dev libsqlite3-dev libssl-dev \
       libtool libuuid1 libyaml-cpp-dev m4 make ninja-build openssh-client \
       openssl patch perl pkg-config procps psmisc python3 python3-dev \
       python3-jsonschema python3-pip python3-venv python3-yaml rsync swig tar \
       uuid-dev vim wget xz-utils zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# The hold branch of vsoch/flux-sched, which has the coschedule policy,
# pinned to the commit the tutorial was tested with. Any branch or commit
# works here.
ARG FLUX_SCHED_REPOSITORY=https://github.com/vsoch/flux-sched.git
ARG FLUX_SCHED_REF=fcc2d5e617ac192f510aadce1a71cbb79af33fce
ARG FLUX_SCHED_VERSION=0.53.0
ARG FLUX_QFW_REPOSITORY=https://github.com/OpenQSE/flux-qfw.git
# A branch or a commit. Pin this to a commit once updates is merged.
ARG FLUX_QFW_REF=updates
RUN set -ex \
    && git clone "${FLUX_SCHED_REPOSITORY}" /tmp/flux-sched \
    && git -C /tmp/flux-sched fetch origin "${FLUX_SCHED_REF}" \
    && git -C /tmp/flux-sched switch --detach FETCH_HEAD \
    && if [ -d /tmp/flux-sched/.git ]; then \
         git -C /tmp/flux-sched describe --always | sed 's/^v//' > /tmp/flux-sched/flux-sched.ver; \
       elif [ ! -f /tmp/flux-sched/flux-sched.ver ]; then \
         echo "${FLUX_SCHED_VERSION}" > /tmp/flux-sched/flux-sched.ver; \
       fi \
    && cat /tmp/flux-sched/flux-sched.ver \
    && cmake -S /tmp/flux-sched -B /tmp/flux-sched/build -G Ninja \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DCMAKE_INSTALL_PREFIX=/usr \
        -DCMAKE_INSTALL_SYSCONFDIR=/etc \
        -DCMAKE_INSTALL_LOCALSTATEDIR=/var \
    && ninja -C /tmp/flux-sched/build \
    && ninja -C /tmp/flux-sched/build install \
    && rm -rf /tmp/flux-sched \
    && test -f /usr/lib/flux/modules/sched-fluxion-qmanager.so \
    && test -f /etc/flux/modprobe/modprobe.d/fluxion.toml

RUN set -ex \
    && git clone "${FLUX_QFW_REPOSITORY}" /tmp/flux-qfw \
    && git -C /tmp/flux-qfw fetch origin "${FLUX_QFW_REF}" \
    && git -C /tmp/flux-qfw switch --detach FETCH_HEAD \
    && git -C /tmp/flux-qfw log --oneline -1 \
    && python3 -m pip install --break-system-packages /tmp/flux-qfw || true \
    && install -d -m 0755 /etc/flux/cli/plugins \
    && install -m 0644 /tmp/flux-qfw/cli-plugins/qfw.py /etc/flux/cli/plugins/qfw.py \
    && rm -rf /tmp/flux-qfw /tmp/vendor \
    && flux-qfw --help >/dev/null \
    && python3 -c 'import flux_qfw.cli_plugin, flux_qfw.scout'

# libfabric, Open MPI 5 with its bundled PRRTE, and flux-pmix. PMIx, hwloc
ARG LIBFABRIC_REF=v2.3.1
ARG LIBFABRIC_PREFIX=/opt/qfw/libfabric
ARG OMPI_VERSION=5.0.9
ARG OMPI_PREFIX=/opt/qfw/openmpi
ARG FLUX_PMIX_REF=v0.7.1

RUN set -ex \
    && git clone https://github.com/ofiwg/libfabric.git /tmp/libfabric \
    && cd /tmp/libfabric \
    && git checkout "${LIBFABRIC_REF}" \
    && ./autogen.sh \
    && ./configure --prefix="${LIBFABRIC_PREFIX}" \
    && make -j"$(nproc)" all \
    && make install \
    && rm -rf /tmp/libfabric

RUN set -ex \
    && export PKG_CONFIG_PATH="${LIBFABRIC_PREFIX}/lib/pkgconfig:${PKG_CONFIG_PATH}" \
    && export CPPFLAGS="-I${LIBFABRIC_PREFIX}/include ${CPPFLAGS}" \
    && export LDFLAGS="-L${LIBFABRIC_PREFIX}/lib ${LDFLAGS}" \
    && ( curl -fsSL -o /tmp/openmpi.tar.bz2 \
           "https://download.open-mpi.org/release/open-mpi/v${OMPI_VERSION%.*}/openmpi-${OMPI_VERSION}.tar.bz2" \
         || curl -fsSL -o /tmp/openmpi.tar.bz2 \
           "https://github.com/open-mpi/ompi/releases/download/v${OMPI_VERSION}/openmpi-${OMPI_VERSION}.tar.bz2" ) \
    && mkdir -p /tmp/ompi \
    && tar --no-same-owner -xjf /tmp/openmpi.tar.bz2 -C /tmp/ompi --strip-components=1 \
    && rm -f /tmp/openmpi.tar.bz2 \
    && cd /tmp/ompi \
    && ./configure --prefix="${OMPI_PREFIX}" --with-libfabric="${LIBFABRIC_PREFIX}" \
        --with-pmix=external --with-hwloc=external --with-libevent=external \
        --with-prrte=internal \
    && make -j"$(nproc)" all \
    && make install \
    && rm -rf /tmp/ompi

RUN set -ex \
    && git clone --depth=1 --branch "${FLUX_PMIX_REF}" \
        https://github.com/flux-framework/flux-pmix.git /tmp/flux-pmix \
    && cd /tmp/flux-pmix \
    && ./autogen.sh \
    && ./configure --prefix=/usr \
    && make -j"$(nproc)" \
    && make install \
    && rm -rf /tmp/flux-pmix \
    && find /usr/lib/flux -name 'pmix*.so' | grep -q .

# QFw, its simulators, and the QRMI/QDMI shim dependencies
ARG QFW_BUILD_JOBS=4
ARG QFW_REPOSITORY=https://github.com/openQSE/QFw.git
# Pinned: locks/qfw-requirements.lock was solved for this commit's setup/
# requirements. Change both together.
ARG QFW_REF=55d13a2096c1789df1404a63f46e9111f3ddf11c
# uv applies setup/overrides.txt, which QFw needs and pip cannot do.
ARG UV_VERSION=0.11.7
ARG QFW_IMAGE_SOURCE=/tmp/qfw-source
ARG QFW_IMAGE_BUILD=/tmp/qfw-build
ARG QFW_IMAGE_PREFIX=/opt/openqse/qfw
ARG QFW_IMAGE_VENV=/opt/openqse/qfw-venv
ARG NWQSIM_PREFIX=/opt/openqse/nwqsim
ARG TNQVM_PREFIX=/opt/openqse/tnqvm
ARG SIMULATOR_WORK_ROOT=/tmp/qfw-simulator-build

ENV PATH=${OMPI_PREFIX}/bin:${LIBFABRIC_PREFIX}/bin:${PATH} \
    LD_LIBRARY_PATH=${OMPI_PREFIX}/lib:${LIBFABRIC_PREFIX}/lib

ARG RUST_VERSION=1.91.0
ENV CARGO_HOME=/opt/qfw/rust/cargo \
    RUSTUP_HOME=/opt/qfw/rust/rustup
RUN set -ex \
    && mkdir -p "${CARGO_HOME}" "${RUSTUP_HOME}" \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
        | sh -s -- -y --no-modify-path --profile minimal \
            --default-toolchain "${RUST_VERSION}" \
    && chmod -R a+rwX /opt/qfw/rust
ENV PATH=${CARGO_HOME}/bin:${PATH}

ARG QRMI_REPO=https://github.com/qiskit-community/qrmi.git
ARG QRMI_VERSION=0.24.4
ARG QRMI_PREFIX=/opt/qfw/qrmi
RUN set -ex \
    && git clone --depth=1 --branch "${QRMI_VERSION}" "${QRMI_REPO}" /tmp/qrmi \
    && cd /tmp/qrmi \
    && cargo build --locked --release --lib \
    && mkdir -p "${QRMI_PREFIX}/lib" "${QRMI_PREFIX}/include" \
    && cp target/release/libqrmi.so "${QRMI_PREFIX}/lib/" \
    && cp qrmi.h "${QRMI_PREFIX}/include/" \
    && rm -rf /tmp/qrmi

RUN set -ex \
    && git -c url.https://github.com/.insteadOf=git@github.com: \
        clone "${QFW_REPOSITORY}" "${QFW_IMAGE_SOURCE}" \
    && git -C "${QFW_IMAGE_SOURCE}" fetch origin "${QFW_REF}" \
    && git -C "${QFW_IMAGE_SOURCE}" switch --detach FETCH_HEAD \
    && git -C "${QFW_IMAGE_SOURCE}" \
        -c url.https://github.com/.insteadOf=git@github.com: \
        submodule update --init --recursive

RUN set -ex \
    && "${QFW_IMAGE_SOURCE}/tools/dependencies/nwqsim/build.sh" \
        --work-dir "${SIMULATOR_WORK_ROOT}/nwqsim" \
        --prefix "${NWQSIM_PREFIX}" \
        --jobs "${QFW_BUILD_JOBS}" \
        --rocm off \
    && test -x "${NWQSIM_PREFIX}/bin/circuit_runner.nwqsim"

RUN set -ex \
    && "${QFW_IMAGE_SOURCE}/tools/dependencies/tnqvm/build.sh" \
        --work-dir "${SIMULATOR_WORK_ROOT}/tnqvm" \
        --prefix "${TNQVM_PREFIX}" \
        --mpi-prefix "${OMPI_PREFIX}" \
        --jobs "${QFW_BUILD_JOBS}" \
        --rocm off \
    && test -x "${TNQVM_PREFIX}/bin/circuit_runner.tnqvm"

# SWIG 4.3 or newer for DEFw's typemaps; Ubuntu noble ships 4.2
ARG SWIG_VERSION=4.3.1
RUN set -ex \
    && apt-get update \
    && apt-get install -y --no-install-recommends libpcre2-dev \
    && apt-get remove -y swig swig4.0 \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL -o /tmp/swig.tar.gz \
        "https://github.com/swig/swig/archive/refs/tags/v${SWIG_VERSION}.tar.gz" \
    && mkdir -p /tmp/swig \
    && tar --no-same-owner -xzf /tmp/swig.tar.gz -C /tmp/swig --strip-components=1 \
    && cd /tmp/swig \
    && ./autogen.sh \
    && ./configure --prefix=/usr/local \
    && make -j"$(nproc)" \
    && make install \
    && rm -rf /tmp/swig /tmp/swig.tar.gz \
    && swig -version | grep -q "SWIG Version ${SWIG_VERSION}"

# Every Python package QFw and the shims need, at exact versions. QFw's
# requirements pin qiskit 2.5 beside a pennylane-qiskit that caps qiskit at
# 2.3, and QFw resolves that with uv and setup/overrides.txt; plain pip cannot.
COPY locks /tmp/locks
RUN set -ex \
    && python3 -m venv "${QFW_IMAGE_VENV}" \
    && "${QFW_IMAGE_VENV}/bin/python" -m pip install --no-cache-dir "uv==${UV_VERSION}" \
    && "${QFW_IMAGE_VENV}/bin/uv" pip install --python "${QFW_IMAGE_VENV}/bin/python" \
        -r /tmp/locks/qfw-requirements.lock \
        --override "${QFW_IMAGE_SOURCE}/setup/overrides.txt" \
    && PATH="${QFW_IMAGE_VENV}/bin:${PATH}" cmake \
        -S "${QFW_IMAGE_SOURCE}" \
        -B "${QFW_IMAGE_BUILD}" \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DCMAKE_INSTALL_PREFIX="${QFW_IMAGE_PREFIX}" \
        -DQFW_BUILD_BUNDLED_DEFW=ON \
    && cmake --build "${QFW_IMAGE_BUILD}" --parallel "${QFW_BUILD_JOBS}" \
    && cmake --install "${QFW_IMAGE_BUILD}" \
    && test -x "${QFW_IMAGE_PREFIX}/bin/qfw-activate" \
    && rm -rf "${QFW_IMAGE_SOURCE}" "${QFW_IMAGE_BUILD}" "${SIMULATOR_WORK_ROOT}"

ENV QFW_PREFIX=${QFW_IMAGE_PREFIX} \
    QFW_VENV=${QFW_IMAGE_VENV} \
    NWQSIM_PREFIX=${NWQSIM_PREFIX} \
    TNQVM_PREFIX=${TNQVM_PREFIX} \
    QRMI_PREFIX=${QRMI_PREFIX} \
    MODULEPATH=/etc/modulefiles:/usr/share/modules/modulefiles \
    LD_LIBRARY_PATH=${OMPI_PREFIX}/lib:${OMPI_PREFIX}/lib64:${QRMI_PREFIX}/lib:${LD_LIBRARY_PATH}

COPY modulefiles /etc/modulefiles
RUN echo /etc/modulefiles >> /etc/environment-modules/modulespath \
    && bash -ex -c '. /usr/share/modules/init/bash \
    && module load libfabric openmpi nwqsim \
    && command -v prte && command -v circuit_runner.nwqsim'

# Flux integration and the tutorial
COPY flux/modprobe/rc1.d/qfw-start-queues.py flux/modprobe/rc1.d/qfw-service-load.py /etc/flux/modprobe/rc1.d/
COPY flux/modprobe/modprobe.d/qfw.toml /etc/flux/modprobe/modprobe.d/qfw.toml
COPY flux/shell/lua.d/qfw-cpu-affinity.lua /etc/flux/shell/lua.d/qfw-cpu-affinity.lua
COPY flux/modules/qfw-service.py /usr/local/lib/flux/modules/qfw-service.py
COPY flux/flux-launch-agent /usr/local/libexec/qfw-flux/
COPY conf /etc/flux/tutorial/conf.d
COPY config/site.yaml /etc/openqse/qfw/site.yaml
COPY config/device-access.yaml config/qpu-users.json /root/.qfw/
COPY tutorial-entrypoint.sh /usr/local/bin/tutorial-entrypoint.sh
COPY qjobs /usr/local/bin/qjobs

# JupyterLab gets its own venv. Installing it into the system Python fails
# because it needs a newer jsonschema than the one apt installed, and pip will
# not remove apt's copy. The venv can still see system packages, so the
# notebook kernel finds Flux's Python bindings.
RUN set -ex \
    && python3 -m venv --system-site-packages /opt/jupyter \
    && /opt/jupyter/bin/python -m pip install --no-cache-dir "uv==${UV_VERSION}" \
    && /opt/jupyter/bin/uv pip install --python /opt/jupyter/bin/python \
        -r /tmp/locks/jupyter-requirements.lock \
    && rm -rf /tmp/locks \
    && /opt/jupyter/bin/jupyter lab --version \
    && /opt/jupyter/bin/python -c 'import jupyter_app_launcher' \
    && /opt/jupyter/bin/python -c 'import flux, flux_qfw'

COPY jupyter-launcher.yaml /usr/local/share/jupyter/lab/jupyter_app_launcher/jp_app_launcher.yaml
COPY assets/flux-icon.png /usr/local/share/jupyter/lab/jupyter_app_launcher/static/flux-icon.png
ENV JUPYTER_APP_LAUNCHER_PATH=/usr/local/share/jupyter/lab/jupyter_app_launcher/ \
    SHELL=/bin/bash

RUN set -ex \
    && chmod 0755 /usr/local/libexec/qfw-flux/flux-launch-agent \
        /usr/local/bin/tutorial-entrypoint.sh \
        /usr/local/bin/qjobs \
    && chmod 0700 /root/.qfw && chmod 0600 /root/.qfw/* \
    && chmod 0644 /etc/openqse/qfw/site.yaml \
    && bash -n /usr/local/libexec/qfw-flux/flux-launch-agent \
    && bash -n /usr/local/bin/tutorial-entrypoint.sh \
    && python3 -m py_compile /etc/flux/modprobe/rc1.d/qfw-start-queues.py \
        /etc/flux/modprobe/rc1.d/qfw-service-load.py /usr/local/lib/flux/modules/qfw-service.py \
    && rm -rf /etc/flux/modprobe/rc1.d/__pycache__ /usr/local/lib/flux/modules/__pycache__ \
    && python3 -c 'import glob, tomllib; [tomllib.load(open(p, "rb")) for p in glob.glob("/etc/flux/tutorial/conf.d/*.toml")]' \
    && flux-qfw add --help >/dev/null

COPY qfw_flux_tutorial.ipynb README.md /tutorial/
COPY demo /tutorial/demo
RUN chmod 0755 /tutorial/demo/*.sh && for f in /tutorial/demo/*.sh; do bash -n "$f"; done
COPY assets /tutorial/assets

ENV FLUX_MODULE_PATH_PREPEND=/usr/local/lib/flux/modules \
    QFW_SITE_CONFIG=/etc/openqse/qfw/site.yaml \
    QFW_DEVICE_ACCESS_CFG=/root/.qfw/device-access.yaml \
    QFW_SHARED_ROOT=/workspace/qfw-container-base \
    QFW_RUN_BASE_DIR=/workspace/qfw-container-base/qfw-runs \
    FLUX_QFW_BACKEND=mock \
    FLUX_QFW_MOCK_SESSION_DELAY=20
RUN mkdir -p /workspace/qfw-container-base/qfw-runs /var/lib/qfw-site-services

WORKDIR /tutorial
EXPOSE 8888
ENTRYPOINT ["/usr/local/bin/tutorial-entrypoint.sh"]
