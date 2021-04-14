If you have Docker available, you can build and run the tutorial with:

```
docker build -t fluxrm/ecp-tutorial:2021
docker run --name flux_tutorial -p 8888:8888 -ti fluxrm/ecp-tutorial:2021
```

Otherwise, the Jupyter Notebook runs some scripts from the
flux-workflow-examples repository, so please ensure that a clone of this exists
in the same location as the ECPTutorial.ipynb notebook. Then launch the jupyter
instance under a running instance of Flux:

```
git clone https://github.com/flux-framework/flux-workflow-examples.git
flux start --size=4 jupyter notebook
```
