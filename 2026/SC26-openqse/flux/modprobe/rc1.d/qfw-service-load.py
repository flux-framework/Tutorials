"""Load the qfw-service broker module at boot (modprobe rc1 drop-in).

modprobe only loads a module something asks for. This asks for qfw-service
(described in modprobe.d/qfw.toml, which names the module file by absolute
path) when the broker config's [qfw] table gives the module something to
run: a directory host, or a QPM with scope = "site" that names a host. With
every device job-scoped, which is this cluster's default, nothing persistent
exists and the module is not loaded. A device behind an external queue needs
no service either: flux-qfw submits a scout job for it.

A broker must still boot when the module file is missing, for example a
container from an image that predates it: then this logs and skips.
"""

import os

MODULE_FILE = os.environ.get(
    "QFW_SERVICE_MODULE", "/usr/local/lib/flux/modules/qfw-service.py"
)


def wants_services(conf):
    if conf.get("directory"):
        return True
    return any(
        spec.get("scope", "site") == "site" and spec.get("host")
        for spec in (conf.get("qpm") or {}).values()
    )


def setup(context):
    conf = context.conf_get("qfw", None)
    if not conf or not wants_services(conf):
        return
    if not os.path.isfile(MODULE_FILE):
        print(f"qfw-service: {MODULE_FILE} not found; the QFw service plane is not loaded")
        return
    context.load_modules(["qfw-service"])
