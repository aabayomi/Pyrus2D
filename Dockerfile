# Start from Ubuntu 20.04
FROM ubuntu:20.04

# Avoid prompts from apt during build
ARG DEBIAN_FRONTEND=noninteractive
ENV DISPLAY docker.for.mac.host.internal:0
ENV RCSS_CONF_DIR /home/rcsoccersim/.rcssserver
ENV LOG_DIR /home/rcsoccersim/logs
ENV TEAM_DIR /home/rcsoccersim/teams
USER root
RUN apt-get update && apt-get upgrade -y

# Install build dependencies for rcssserver and soccerwindow2, including common dependencies
RUN apt-get install -y build-essential git autoconf libtool qt5-default libqt5opengl5-dev libaudio-dev libxt-dev libxi-dev libxmu-dev libpng-dev libglib2.0-dev libfontconfig1-dev libxrender-dev libxext-dev

RUN apt-get update && apt-get install -y flex automake autoconf libtool flex bison libboost-all-dev

# Clone, build, and install rcssserver
WORKDIR /root
RUN git clone https://github.com/rcsoccersim/rcssserver.git

WORKDIR /root/rcssserver
RUN autoreconf -i && ./configure && make && make install && ldconfig

RUN mkdir -p /root/src
WORKDIR /root/src
RUN git clone  https://github.com/helios-base/librcsc.git \
    && cd librcsc \
    && ./bootstrap \
    && ./configure --disable-unit-test \
    && make \
    && make install && ldconfig


WORKDIR /root/src
RUN git clone  https://github.com/helios-base/soccerwindow2.git \
    && cd soccerwindow2 \
    && autoreconf -i \
    && ./configure \
    && make \
    && make install && ldconfig


RUN apt-get update && apt-get install -y wget git bzip2 && \
    rm -rf /var/lib/apt/lists/*



RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -O /miniconda.sh && \
    bash /miniconda.sh -b -p /miniconda && \
    rm /miniconda.sh

# Add Conda to PATH
ENV PATH="/miniconda/bin:${PATH}"

# Create a Conda environment named 'keepaway' with Python 3.11
RUN conda create -y --name keepaway python=3.11


# Cleanup to reduce image size
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


RUN useradd -d /home/rcsoccersim -m -s /bin/bash rcsoccersim \
  && echo "rcsoccersim:rcsoccersim" | chpasswd
RUN mkdir -p $RCSS_CONF_DIR $TEAM_DIR $LOG_DIR
RUN chown -R rcsoccersim:rcsoccersim /home/rcsoccersim
USER rcsoccersim

VOLUME $TEAM_DIR
VOLUME $LOG_DIR

WORKDIR $TEAM_DIR

## install keepaway 

RUN git clone https://github.com/aabayomi/Pyrus2D.git \ 
      && cd Pyrus2D
SHELL ["conda", "run", "-n", "keepaway", "/bin/bash", "-c"] 

WORKDIR $TEAM_DIR/Pyrus2D

COPY entrypoint.sh /usr/local/bin/entrypoint.sh

#COPY requirements.txt /tmp/
#RUN conda install --no-cache-dir -r requirements.txt
# Assume the Conda environment "keepaway" is already created
RUN conda run -n keepaway /bin/bash -c "pip install --no-cache-dir -r requirements.txt"

RUN conda run -n keepaway /bin/bash -c "pip install -e ."

WORKDIR $TEAM_DIR/Pyrus2D/keepaway

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

CMD ["conda", "run", "-n", "keepaway", "python3", "examples/training_agent.py --gc=3v2 --policy=handcoded --num_episodes=1000000"]

