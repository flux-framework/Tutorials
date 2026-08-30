#!/usr/bin/env python3
"""Build the SC26 tutorial notebooks from the 2026/HPCIC-AWS sources.

Rerun this to regenerate module notebooks after editing the upstream chapters.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent / "Tutorials" / "2026"
SRC = ROOT / "HPCIC-AWS" / "tutorial"
DST = ROOT / "SC26" / "tutorial"

# Flux brand blues, taken from assets/Flux-logo.svg, plus warm pizza accents.
DEEP = "#036291"
LIGHT = "#91C2D8"
PALE = "#DCECF4"
CRUST = "#D9A441"
INK = "#06293D"


def banner(module, title, subtitle):
    """Return the markdown source for a module title banner."""
    return f"""<div>
<center><img src="../assets/Flux-logo.svg" width="360"/></center>
</div>

<div style="background:linear-gradient(90deg,{DEEP} 0%,{LIGHT} 100%);padding:20px 26px;border-radius:10px;border-left:10px solid {CRUST};margin-top:18px">
<h1 style="margin:0;color:#ffffff">Module {module}: {title}</h1>
<p style="margin:6px 0 0 0;color:{PALE};font-size:15px">{subtitle}</p>
<p style="margin:2px 0 0 0;color:{PALE};font-size:13px">SC26 &middot; Chicago &middot; November 2026</p>
</div>"""


def callout(label, text, color=LIGHT):
    """Return the markdown source for a colored description callout."""
    return (
        f'<div class="alert alert-block" style="background-color:{color};color:{INK}">\n'
        f'<span style="font-weight:600">{label}:</span> {text}\n'
        "</div>"
    )


def badge(text):
    """Return the markdown source for an end-of-section completion badge."""
    return (
        f'<div style="background:{PALE};border-left:6px solid {CRUST};'
        f'padding:12px 18px;color:{INK}"><strong>{text}</strong></div>'
    )


def load(path):
    with open(path) as fh:
        return json.load(fh)


def save(nb, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(nb, fh, indent=1)
        fh.write("\n")
    print(f"wrote {path.relative_to(ROOT.parent)}")


def md(source):
    """Return a new markdown cell."""
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(True)}


def code(source):
    """Return a new code cell."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(True),
    }


def apply_edits(nb, edits):
    """Apply literal string replacements across every cell in a notebook."""
    for cell in nb["cells"]:
        text = "".join(cell["source"])
        for old, new in edits:
            text = text.replace(old, new)
        cell["source"] = text.splitlines(True)
    return nb


NB_META = {
    "kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.10.12"},
}


def notebook(cells):
    """Wrap a cell list in notebook v4 structure."""
    return {"cells": cells, "metadata": NB_META, "nbformat": 4, "nbformat_minor": 5}


COMMON = [
    ("2026/HPCIC-AWS", "2026/SC26"),
    ("/home/ubuntu/tutorial/ch1", "/home/ubuntu/tutorial/module1"),
    ("/home/ubuntu/tutorial/ch2", "/home/ubuntu/tutorial/module1"),
    ("/home/ubuntu/tutorial/ch3", "/home/ubuntu/tutorial/module1"),
    ("/ch2", "/module1"),
    ('style="background-color:skyblue"', f'style="background-color:{LIGHT};color:{INK}"'),
    ('style="background-color:lightgreen"', f'style="background-color:{PALE};color:{INK}"'),
    (
        'style="background-color:rebeccapurple; color: white"',
        f'style="background-color:{DEEP};color:#ffffff"',
    ),
]

PIZZA = [
    ("/tmp/harry-potter.txt", "/tmp/deep-dish.txt"),
    ('echo \\"Yer a wizard, $(whoami)!\\"', 'echo \\"Order up for $(whoami)!\\"'),
    ('echo "Yer a wizard, $(whoami)!"', 'echo "Order up for $(whoami)!"'),
    ("::: harry ron hermione", "::: sausage giardiniera mozzarella"),
    ("--job-name magic", "--job-name deepdish"),
    ("--job-name moremagic", "--job-name extracheese"),
    ("moremagic:F", "extracheese:F"),
    ("magic:F", "deepdish:F"),
    ('"Wingardium Leviosa! \\u2728\\ufe0f"', '"Ope, just gonna squeeze past ya"'),
]


def build_module1_01():
    nb = load(SRC / "ch1" / "01_flux_tutorial.ipynb")
    apply_edits(nb, COMMON + PIZZA)

    nb["cells"][0] = md(
        banner(
            1,
            "Flux Foundations &amp; Hierarchical Scheduling",
            "Submitting work, batch jobs, and the porcelain commands",
        )
    )

    nb["cells"][1] = md(
        """# Welcome to the Flux Tutorial

> What is Flux Framework? \U0001f914\ufe0f

Flux is a flexible framework for resource management, built for your site. The framework consists of a suite of projects, tools, and libraries that may be used to build site-custom resource managers for High Performance Computing centers and cloud environments. Flux is a next-generation resource manager and scheduler with many transformative capabilities like hierarchical scheduling and resource management (you can think of it as "fractal scheduling") and directed-graph based resource representations.

## How this tutorial is organized

| Module | What you will do |
|---|---|
| **1. Foundations** | Submit jobs, run batch scripts, build a hierarchy, write a plugin |
| **2. Converged Environments** | Flux in the cloud, Usernetes, Kubeflow Trainer, quantum simulation |
| **3. Open Forum** | Lightning talks, trivia, and terrible jokes |

Module 1 has three notebooks: this one, then the [Python SDK](02_flux_python_sdk.ipynb), then [instances, internals, and plugins](03_flux_instances_and_plugins.ipynb).

## Set up your workspace

Click on <button data-commandLinker-command="terminal:open" data-name="flux" href="#">this button</button> to create a Terminal. Drag it to sit alongside this notebook, so you have the terminal on the left and this text on the right.

Every command in this notebook is meant to be **copied into that terminal**. The notebook is the recipe card; the terminal is the kitchen.

```bash
cd /home/ubuntu/tutorial/module1
```
"""
    )

    for cell in nb["cells"]:
        text = "".join(cell["source"])
        if text.startswith("### The Flux Hierarchy"):
            text = text.replace(
                "### The Flux Hierarchy \U0001f347\ufe0f",
                """### The Flux Hierarchy \U0001f355\ufe0f

> A Chicago deep dish is built in layers, and each layer does its own job. You do not ask
> the crust to also be the cheese.
>
> A single-queue scheduler is a flat pizza: one surface, one thing happening on it, and
> throughput bounded by how fast that surface can work. Flux lets you add a layer, and
> each layer schedules independently. `flux uptime` tells you which layer you are
> standing on (`depth 0` is the pan).""",
            )
            cell["source"] = text.splitlines(True)

    puzzle = md(
        """<br>

## \U0001f9e9 The Oven Packing Puzzle

"""
        + callout(
            "Competition",
            "First correct answer with a working command wins a prize. "
            "Start with <code>flux resource list</code> to see what you have.",
            CRUST,
        )
        + """

Here is your order. Six pizzas, each needing a different number of cores and a different
bake time:

| Pizza | Cores | Bake time |
|---|---|---|
| margherita | 1 | 20s |
| pepperoni | 1 | 20s |
| deep dish | 4 | 30s |
| sicilian | 4 | 30s |
| calzone | 2 | 10s |
| stromboli | 2 | 10s |

**The challenge:** submit all six as Flux jobs so the whole order completes as fast as
possible. Use `flux submit` with `--cores-per-task`, and `sleep` to stand in for the bake.
Give each job a `--job-name` so you can see it.

One pizza to get you started:

```bash
flux submit --cores-per-task=1 --job-name margherita sleep 20
```

Then watch the whole order:

```bash
flux watch --all
```

"""
        + callout(
            "Think about it",
            "The naive answer is to submit them in the order listed. Is that fastest? "
            "What is the theoretical floor, given your core count? What changes if you "
            "submit the two 4-core pizzas first?",
            PALE,
        )
        + """

<!-- TODO(sc26): work out the optimal ordering and the makespan floor for the core count
     the tutorial image actually provides, then write the answer key. Do not guess the
     core count; it differs between the local kind image and the EC2 instances. -->
"""
    )
    nb["cells"].insert(len(nb["cells"]) - 1, puzzle)

    nb["cells"][-1] = md(
        badge("Module 1, Notebook 1 complete")
        + """

## What you covered

1. Getting help and listing resources
2. `flux run`, `flux submit`, `flux bulksubmit`, and `flux watch`
3. `flux alloc` and `flux batch`, and how batch creates a nested instance
4. Reading the hierarchy with `flux pstree`
5. Packing an oven

Next: the [Python Submission API](02_flux_python_sdk.ipynb), the one notebook where you
run cells directly instead of copying to a terminal.
"""
    )
    save(nb, DST / "module1" / "01_flux_foundations.ipynb")


def build_module1_02():
    nb = load(SRC / "ch2" / "02_flux_framework.ipynb")
    apply_edits(nb, COMMON + PIZZA)

    nb["cells"][0] = md(
        banner(1, "The Flux Python SDK \U0001f40d\ufe0f", "Submitting and watching jobs programmatically")
        + "\n\n"
        + callout(
            "Run these",
            "This is the one notebook with executable cells. Everything else is "
            "copy-paste into a terminal, because commands like <code>flux top</code> "
            "and <code>flux alloc</code> need a real TTY.",
            PALE,
        )
    )

    # The KVS example moves here from ch3: it is Python SDK material, and module 1's
    # other notebooks are terminal-driven markdown only.
    kvs_src = None
    for cell in load(SRC / "ch3" / "03_flux_tutorial.ipynb")["cells"]:
        if cell["cell_type"] == "code" and "flux.kvs" in "".join(cell["source"]):
            kvs_src = "".join(cell["source"])
    if kvs_src:
        header = callout(
            "Description",
            "The Flux key-value store underpins most of Flux's own services. "
            "Here it is from the Python bindings.",
            DEEP,
        ).replace(f"color:{INK}", "color:#ffffff")
        nb["cells"].insert(len(nb["cells"]) - 1, md("### The KVS from Python\n\n" + header))
        nb["cells"].insert(len(nb["cells"]) - 1, code(kvs_src))

    nb["cells"][-1] = md(
        badge("Module 1, Notebook 2 complete")
        + "\n\nNext: [instances, internals, and plugins](03_flux_instances_and_plugins.ipynb).\n"
    )
    save(nb, DST / "module1" / "02_flux_python_sdk.ipynb")


def build_module1_03():
    nb = load(SRC / "ch3" / "03_flux_tutorial.ipynb")
    apply_edits(nb, COMMON + PIZZA)

    # Module 1 is terminal-driven, so convert the inherited code cells. The KVS
    # example moved to notebook 02; flux dmesg becomes a copy-paste block.
    cells = []
    for cell in nb["cells"]:
        text = "".join(cell["source"])
        if cell["cell_type"] == "code":
            if "flux.kvs" in text:
                continue
            cells.append(md("```bash\n" + text.replace("!", "", 1).strip() + "\n```"))
        else:
            cells.append(cell)
    nb["cells"] = cells

    nb["cells"][0] = md(
        banner(1, "Instances, Internals, and Plugins", "The plumbing under the porcelain, and how to extend it")
        + """

Now that we have covered the basic commands and hierarchical scheduling, let's look at
the structure of an individual Flux instance and the services that make it run:

1. Process and monitoring utilities
2. The structure of Flux instances
3. `flux kvs`, which powers a lot of the higher level commands
4. `flux archive` for sites without a shared filesystem
5. Writing your own job validator plugin, in Python

```bash
cd /home/ubuntu/tutorial/module1
```
"""
    )

    workshop = md(
        """<br>

# \U0001f527 Plugin Workshop: Write a Job Validator

"""
        + callout(
            "Description",
            "Extending Flux in Python. No compiler, no root, no restarting the instance.",
            CRUST,
        )
        + """

Flux has several extension points, and they are not all the same language:

| Extension point | Language | What it controls |
|---|---|---|
| **Job validator** | **Python** | Whether a job is admitted at all |
| Job shell plugin | Lua or C | What happens when tasks launch |
| Jobtap plugin | C only | Scheduling policy and priority |
| `flux` subcommand | Anything executable | New commands |

We are doing the Python one. Every job submitted to this instance passes through
the validator before it reaches the scheduler, so this is where site policy lives:
core limits, banned commands, "please use flux batch for anything this big."

A validator plugin is one class with one required method:

```python
from flux.job.validator import ValidatorPlugin

class Validator(ValidatorPlugin):
    def validate(self, job):
        # return None to accept, or (errno, message) to reject
```

The `job` argument gives you `job.jobspec` (the submitted jobspec as a plain dict),
plus `job.userid`, `job.flags`, and `job.urgency`. To count resources, hand the
jobspec to `JobspecV1` and call `resource_counts()`, which returns a dict like
`{"node": 1, "slot": 4, "core": 8}` with nested counts already multiplied out.

## The skeleton

Open [plugin-workshop/pizza_policy.py](plugin-workshop/pizza_policy.py). The class and
the resource lookups are written; the decision is yours.

## Test it without touching the instance

`flux run --dry-run` prints a jobspec instead of submitting it, so you can pipe one
straight into the validator. This is a fast edit-and-rerun loop:

```bash
cd /home/ubuntu/tutorial/module1
flux run --dry-run -n4 sleep 60 | flux job-validator --jobspec-only --plugins=./plugin-workshop/pizza_policy.py
```

A passing job prints an errnum of 0. A rejected one prints your message.

Try the worked example, which caps cores and refuses a couple of toppings:

```bash
flux run --dry-run -n8 sleep 60 | flux job-validator --jobspec-only --plugins=./plugin-workshop/oven_capacity.py --max-cores=4
```

```console
{"errnum": 22, "errstr": "order needs 8 cores, the oven fits 4"}
```

## Then load it for real

```bash
flux module reload job-ingest validator-plugins=jobspec,$(pwd)/plugin-workshop/oven_capacity.py
```

Now ordinary submission goes through it:

```bash
flux submit -n8 sleep 60
```

Put things back when you are done:

```bash
flux module reload job-ingest validator-plugins=jobspec
```

"""
        + callout(
            "Your turn",
            "Cap the core count. Reject a command by name and say why. Require every job "
            "to have a <code>--job-name</code>. Only accept work during business hours. "
            "Reject anything asking for zero nodes, on principle. We will share the best "
            "ones at the start of Module 3.",
            PALE,
        )
        + """

<!-- TODO(sc26): smoke-test against the tutorial image. The interface is from
     flux-core v0.86.0 (the version build-ubuntu.sh installs): ValidatorPlugin and
     ValidatorJobInfo in src/bindings/python/flux/job/validator/validator.py, and the
     validator-plugins=<path> form is exercised by t/t2110-job-ingest-validator.t.
     Both plugin files were tested against the basic_v1.yaml jobspec fixture with a
     faithful port of resource_counts, but not yet against a live job-ingest module.
     The notebook runs under `flux start --test-size=4`, so confirm whether the module
     reload needs `flux exec -r all -x 0` as the flux-core test helper does. -->

## If you would rather write Lua

The job shell is the other user-facing extension point, and it takes inline Lua plugins
registered with `plugin.register` in an initrc. Where the validator decides *whether* a
job runs, a shell plugin decides *what happens* when its tasks launch.

[plugin-workshop/oven-timer.lua](plugin-workshop/oven-timer.lua) is a skeleton and
[plugin-workshop/order-ticket.lua](plugin-workshop/order-ticket.lua) is a complete
example. Neither needs installing:

```bash
flux run -o verbose=2 -o userrc=plugin-workshop/order-ticket.lua -n2 hostname
```

## Where to read more

- `flux-job-validator(1)` and `flux-config-ingest(5)` for the validator
- `flux-shell-initrc(5)` for the Lua shell plugin API
- `flux-jobtap(1)` for scheduling policy, if you are comfortable in C
- `flux-environment(7)`, `FLUX_EXEC_PATH` &mdash; drop an executable named `flux-something`
  on that path and it becomes `flux something`, in any language you like
"""
    )
    nb["cells"].insert(len(nb["cells"]) - 1, workshop)

    nb["cells"][-1] = md(
        badge("Module 1 complete")
        + "\n\nContinue to [Module 2: Converged Environments](../module2/01_flux_operator_cloud.ipynb).\n"
    )
    save(nb, DST / "module1" / "03_flux_instances_and_plugins.ipynb")


def _ch4_cell(prefix):
    """Return the ch4 markdown cell whose text starts with prefix, with edits applied."""
    ch4 = load(SRC / "ch4" / "04_flux_framework_usernetes.ipynb")
    apply_edits(ch4, COMMON + PIZZA)
    for cell in ch4["cells"]:
        text = "".join(cell["source"])
        if text.startswith(prefix):
            return text
    raise RuntimeError(f"ch4 cell not found: {prefix!r} (did the upstream heading move?)")


def build_module2_01():
    """Usernetes. This is the substrate everything else in module 2 runs on."""
    body = _ch4_cell("## 1. Start Usernetes")
    body = body.replace("## 1. Start Usernetes", "## 1. Start the control plane")

    cells = [
        md(
            banner(2, "Usernetes: Kubernetes in User Space", "Bringing up a control plane inside a Flux job")
            + """

Converged computing, on-premises. You have a cluster with Flux as the system scheduler,
and you want Kubernetes-native workloads on it without asking an administrator for a
cluster.

Usernetes is Kubernetes running entirely in user space, launched as a Flux job. Nothing
here needs a cloud account, and nothing here needs root.

<div>
<center><img src="img/flux-usernetes-turkducken.png" width="620"/></center>
</div>

Everything in Module 2 builds on this notebook. The Flux Operator in the next notebook
gets installed *into* the cluster you are about to start, and the Kubeflow Trainer after
that goes into the same one.
"""
        ),
        md(body),
        md(
            badge("Module 2, Notebook 1 complete")
            + "\n\nNext: [the Flux Operator, installed into this cluster](02_flux_operator.ipynb).\n"
        ),
    ]
    save(notebook(cells), DST / "module2" / "01_usernetes.ipynb")


def build_module2_02():
    """LAMMPS bare metal, then the Flux Operator inside the usernetes cluster."""
    body = _ch4_cell("## 2. Run LAMMPS with Flux")
    body = body.replace("cd tutorial/ch4/", "cd /home/ubuntu/tutorial/module2")
    body = body.replace(
        "kubectl apply -f flux-minicluster-lammps.yaml",
        "kubectl apply -f ./manifests/flux-minicluster-lammps.yaml",
    )
    body = body.replace(
        "kubectl delete -f ./flux-minicluster-lammps.yaml",
        "kubectl delete -f ./manifests/flux-minicluster-lammps.yaml",
    )
    body = body.replace("previous tutorial", "Module 1")

    cells = [
        md(
            banner(2, "The Flux Operator, Inside Usernetes", "Turducken: Flux in Kubernetes, in a Flux job")
            + """

The cluster from the last notebook is running. Now we put Flux back inside it.

First LAMMPS the ordinary way, straight through the Flux instance the notebook is already
running in. Then the same LAMMPS run as a MiniCluster, scheduled by a Flux instance that
the Flux Operator brings up inside Usernetes, which is itself a Flux job.
"""
        ),
        md(body),
        md(
            callout(
                "Architecture note",
                "The operator manifest above is the <strong>ARM</strong> build, and the "
                "MiniCluster uses an ARM Flux view with a LAMMPS image built for AWS EFA "
                "on Graviton. These are matched to the EC2 instance. They will not run on "
                "an x86 machine.",
                CRUST,
            )
        ),
        md(
            badge("Module 2, Notebook 2 complete")
            + "\n\nNext: [Kubeflow Trainer](03_kubeflow_trainer.ipynb), into the same cluster.\n"
        ),
    ]
    save(notebook(cells), DST / "module2" / "02_flux_operator.ipynb")


def build_module2_03():
    """Kubeflow Trainer, carried over from the ch4 AI/ML sections."""
    install = _ch4_cell("## 3. Run an AI/ML Training Job").replace(
        "## 3. Run an AI/ML Training Job", "## 1. Install the Kubeflow Trainer"
    )
    mnist = (
        _ch4_cell("### Run MNIST")
        .replace("### Run MNIST", "## 2. Run MNIST")
        .replace("pytorch-mnist.yaml](pytorch-mnist.yaml)", "pytorch-mnist.yaml](manifests/pytorch-mnist.yaml)")
        .replace("./pytorch-mnist.yaml", "./manifests/pytorch-mnist.yaml")
        .replace("kubectl delete -f pytorch-mnist.yaml", "kubectl delete -f ./manifests/pytorch-mnist.yaml")
    )

    cells = [
        md(
            banner(2, "Kubeflow Trainer", "AI/ML and HPC simulation from one control plane")
            + """

Same Usernetes cluster, third thing installed into it. The
[Kubeflow Trainer](https://www.kubeflow.org/docs/components/trainer/getting-started/) runs
AI/ML workloads in Kubernetes directly from Python. We start with a plain PyTorch training
job, then swap in the Flux runtime so the same `TrainJob` abstraction launches an MPI
simulation instead.
"""
        ),
        md(install),
        md(mnist),
        md(
            "## 3. Now the same abstraction, but for HPC\n\n"
            + callout(
                "Description",
                "A <code>TrainJob</code> that runs LAMMPS instead of PyTorch, with Flux bootstrapping the ranks.",
            )
            + """

This LAMMPS example assumes two small nodes. Retrieve and alter the manifest to increase
the problem size if you have more.

```bash
kubectl apply --server-side -f https://raw.githubusercontent.com/kubeflow/trainer/refs/heads/master/examples/flux/flux-runtime.yaml
kubectl apply -f https://raw.githubusercontent.com/kubeflow/trainer/refs/heads/master/examples/flux/lammps-train-job.yaml
```

<!-- TODO(sc26): this section came from 2026/HPSF, where it ran on a two-node EKS cluster.
     Confirm it works on the single-node ARM usernetes setup, and confirm the images have
     ARM builds. If not, either pin an ARM manifest or cut the section. -->
"""
        ),
        md(
            """## 4. Monitor and read the logs

```bash
kubectl get pods -w
```

The lead broker is pod index `0-0`. Watch it bootstrap and then run LAMMPS:

```bash
kubectl logs lammps-flux-node-0-0-<suffix> -c node -f
```

Same `TrainJob` resource, same control plane. Only the runtime changed.
"""
        ),
        md(badge("Module 2, Notebook 3 complete") + "\n\nNext: [Quantum simulation under Flux](04_quantum_local.ipynb).\n"),
    ]
    save(notebook(cells), DST / "module2" / "03_kubeflow_trainer.ipynb")


def build_module2_04():
    cells = [
        md(
            banner(2, "Hybrid Quantum-Classical Under Flux", "A local simulator, no cloud account, no hardware queue")
            + """

So far Flux has scheduled classical HPC, AI/ML training, and a Kubernetes control plane.
Here we add a quantum workload, and the point is that **nothing about Flux changes**. A
hybrid quantum-classical algorithm is a classical optimizer wrapped around a circuit
evaluation. That loop is a job. Flux schedules jobs.

Everything runs on the CPU cores Flux gave you, via `qiskit-aer`. No account, no
credentials, no waiting in a hardware queue.
"""
        ),
        md(
            """## Background: QAOA max-cut

**Max-cut** asks: given a graph, split its nodes into two groups so that as many edges as
possible run *between* the groups rather than inside them. It is NP-hard.

**QAOA** (the Quantum Approximate Optimization Algorithm) encodes each node as a qubit and
builds a parameterized circuit with two alternating layers: a cost layer with parameter
`gamma`, and a mixer layer with parameter `beta`. Measuring gives bitstrings, each a
candidate partition. A classical optimizer then adjusts `gamma` and `beta` to push the
average cut up.

We are splitting an order of pizzas across two ovens. Each edge is a pair of orders that
should not share an oven.
"""
        ),
        md(
            """## 1. Check the simulator

```bash
cd /home/ubuntu/tutorial/module2
python3 -c "import qiskit, qiskit_aer; print(qiskit.__version__, qiskit_aer.__version__)"
```

If those are missing:

```bash
pip install --user qiskit qiskit-aer scipy
```
"""
        ),
        md(
            "## 2. Run it under Flux\n\n"
            + callout("Description", "<code>flux run</code> blocks and streams output, exactly as in Module 1.")
            + """

```bash
flux run --cores-per-task=1 python3 scripts/qaoa_maxcut.py -p 2 -s 2048
```

```console
{
  "layers": 2,
  "shots": 2048,
  "evaluations": 40,
  "mean_cut": 4.841,
  "best_bitstring": "01001",
  "best_cut": 6,
  "max_possible_edges": 7,
  "oven_a": [1, 2, 4],
  "oven_b": [0, 3]
}

Oven A: orders [1, 2, 4]
Oven B: orders [0, 3]
Separated 6 of 7 conflicting pairs.
```

Six is the true optimum for this graph, which you can confirm by brute force over all 32
partitions. QAOA found it without enumerating them.
"""
        ),
        md(
            """## 3. Sweep the depth

The interesting question is how the answer changes with circuit depth `p`. That is a
parameter sweep, which is the thing Flux is best at:

```bash
flux bulksubmit --watch python3 scripts/qaoa_maxcut.py -p {} ::: 1 2 3 4 5
```

Or use `--cc` to run the same depth repeatedly with different seeds:

```bash
flux submit --cc=1-8 --watch python3 scripts/qaoa_maxcut.py -p 3 --seed {cc}
```

"""
            + callout(
                "Notice",
                "More layers is not automatically better. Deeper circuits mean more "
                "parameters for the classical optimizer to fit from the same number of "
                "shots. This is exactly the kind of trade-off you want a scheduler to let "
                "you explore cheaply.",
                PALE,
            )
        ),
        md(
            badge("Module 2 complete")
            + """

## Cleaning up

Module 2 is done, so bring the Usernetes cluster back down:

```bash
kubectl delete all --all
make -C /home/ubuntu/usernetes down
```

Continue to [Module 3](../module3/01_wrapup_and_resources.ipynb).
"""
        ),
    ]
    save(notebook(cells), DST / "module2" / "04_quantum_local.ipynb")


def build_module3():
    cells = [
        md(banner(3, "Lightning Talks, Trivia, and Open Forum", "Research, terrible jokes, and where to go next")),
        md(
            """## Lightning talks

<!-- TODO(sc26): fill in speakers and titles once confirmed.

       - Flux plugins and development
       - Flux from the HPC admin perspective
       - Real-world R&D: scheduling, eBPF, storage, workflows
-->
"""
        ),
        md(
            """## Plugin show and tell

Before trivia, we look at what people built in the Module 1 plugin workshop. Bring your
`.lua` file.
"""
        ),
        md(
            """## Deep Dish Trivia \U0001f355

Teams of four. The board goes up on the big screen: [`trivia/index.html`](trivia/index.html).

Four rounds, with a joke between each one:

1. **Is this a real flux subcommand?**
2. **Flux internals**
3. **HPC history**
4. **Chicago and pizza**

It is a single static page with no dependencies, so it also works offline when the
conference wifi does what conference wifi does.
"""
        ),
        md(
            """## Joining the Flux community

| Where | What for |
|---|---|
| [flux-framework on GitHub](https://github.com/flux-framework) | Issues, pull requests, and the code |
| [Documentation](https://flux-framework.readthedocs.io) | Reference and the learning guide |
| [Learning guide](https://flux-framework.readthedocs.io/en/latest/guides/learning_guide.html) | The long-form introduction |
| [High Performance Software Foundation](https://hpsf.io) | Flux's foundation home |

<!-- TODO(sc26): add the Slack/Matrix invite link and the SC26 survey URL. -->
"""
        ),
        md(badge("That's the tutorial. Thanks for coming to Chicago.")),
    ]
    save(notebook(cells), DST / "module3" / "01_wrapup_and_resources.ipynb")


if __name__ == "__main__":
    if not SRC.exists():
        sys.exit(f"source tree not found: {SRC}")
    build_module1_01()
    build_module1_02()
    build_module1_03()
    build_module2_01()
    build_module2_02()
    build_module2_03()
    build_module2_04()
    build_module3()
