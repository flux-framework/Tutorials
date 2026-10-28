#!/bin/bash
# Start the tutorial: build R for a nine broker instance (flux-lead and c1
# through c8), then run that instance with JupyterLab as its initial
# program. When Jupyter exits, the instance shuts down with it.
#
#   TUTORIAL_BROKERS  brokers to start (default 9: flux-lead and c1..c8)
#   TUTORIAL_PORT     port Jupyter listens on inside the container (8888)
#   QFW_QPUS          replace the default devices, as NAME[=QPUS][:QUBITS],
#                     for example "nwqsim:32 fake-iqm=2:20"
set -euo pipefail

BROKERS="${TUTORIAL_BROKERS:-9}"
PORT="${TUTORIAL_PORT:-8888}"
CONF_DIR=/etc/flux/tutorial/conf.d
R_FILE=/etc/flux/tutorial/R.json
QPUS="${QFW_QPUS:-nwqsim:32 fake-iqm=2:20 iqm-ornl-20q:20 shim-ornl-20q:20}"
work="$(mktemp -d)"

# flux start sets FLUX_URI for Jupyter; drop any value inherited from the
# base image
unset FLUX_URI

# the nodes: flux-lead plus c1..c8, four cores each, c1..c8 in the normal
# queue
hosts="flux-lead"
if [ "${BROKERS}" -gt 1 ]; then
    hosts="flux-lead,c[1-$((BROKERS - 1))]"
fi
flux R encode --hosts="${hosts}" --cores=0-3 --property="normal:1-$((BROKERS - 1))" > "${work}/nodes.json"

# the scheduling graph and the QPM device vertices. flux-qfw builds the
# graph with flux ion-R encode, then adds a qdevice -> qpu -> qubit subtree
# per device beside the nodes.
# shellcheck disable=SC2086
flux-qfw add --r "${work}/nodes.json" --output "${R_FILE}" ${QPUS}
chmod 0644 "${R_FILE}"
rm -rf "${work}"

export FLUX_QFW_BACKEND="${FLUX_QFW_BACKEND:-mock}"
echo "---> Starting a ${BROKERS} broker Flux instance (${hosts}) with JupyterLab on port ${PORT} ..."
# JupyterLab opens on the Launcher, which has a card for the notebook. Its
# terminals run bash (SHELL in the image) in /tutorial and inherit FLUX_URI
# from flux start, so the commands in the notebook work as pasted.
exec flux start -s "${BROKERS}" -o,--config-path="${CONF_DIR}" \
    /opt/jupyter/bin/jupyter lab --ip=0.0.0.0 --port="${PORT}" --no-browser --allow-root \
        --ServerApp.token='' --ServerApp.password='' \
        --ServerApp.root_dir=/tutorial "$@"
