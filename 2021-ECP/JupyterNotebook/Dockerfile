FROM fluxrm/flux-sched:focal
MAINTAINER patki1@llnl.gov

RUN pip3 install jupyterlab \
    && echo "export PATH=$HOME/.local/bin:$PATH" >> "$HOME/.bashrc"

RUN git clone https://github.com/flux-framework/flux-workflow-examples.git

COPY ECPTutorial.ipynb .
COPY sleep_batch.sh .

EXPOSE 8888
CMD flux start --size=4 /home/fluxuser/.local/bin/jupyter notebook --ip 0.0.0.0
