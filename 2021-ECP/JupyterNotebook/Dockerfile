#This is a sample Image 
FROM fluxrm/flux-sched:focal
MAINTAINER patki1@llnl.gov

#ENV TZ="America/Los_Angeles"
#ENV DEBIAN_FRONTEND="noninteractive"
#RUN apt-get update && apt-get 

RUN pip3 install jupyterlab \
    && echo "export PATH=$HOME/.local/bin:$PATH" >> "$HOME/.bashrc"

#ENV DISPLAY=host.docker.internal:0

RUN git clone https://github.com/flux-framework/flux-workflow-examples.git

#Set up the jupyter notebook 
COPY ECPTutorial.ipynb .
COPY sleep_batch.sh .

EXPOSE 8888
CMD flux start --size=4 /home/fluxuser/.local/bin/jupyter notebook --ip 0.0.0.0
