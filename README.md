# RoboCup Soccer Keepaway Python Implementation

This package contains a python based RL environment of the RoboCup Keepaway suitable for research purpose. Designed at UT Austin.

Useful Links

* [Keepaway c++](https://github.com/tjpalmer/keepaway) - Run the alternate c++ version of keepaway.
* [Gregory Kuhlmann and Peter Stone](https://www.cs.utexas.edu/~pstone/Papers/bib2html/b2hd-AB05.html) - Keepaway Paper
* [CYRUS](https://arxiv.org/abs/2211.08585) Python based RoboCup 2D soccer simulator.
* [RoboCup ](https://www.robocup.org/)
[Soccer Simulation 2D League](https://rcsoccersim.github.io/) 2D simulation League
* [Server documentation](https://rcsoccersim.readthedocs.io/) RCSSServer Documentation


The framework includes all low and mid-level keepaway behaviors. However, the framework was designed to make it easy to insert your own learning code for deep reinforcement learning.


``` utils/ ```

```shell
keepaway/
    utils/
```

---
## Quick Start 

### Run in On Linux Computer

#### 1. Install required simulator dependencies 

This code has only been tested on Linux, the rcssserver and rcssmonitor only support Linux/Ubuntu.

Install rcssserver and rcssmonitor (soccer window for debugging proposes)

- rcssserver: [https://github.com/rcsoccersim/rcssserver](https://github.com/rcsoccersim/rcssserver)
- rcssmonitor: [https://github.com/rcsoccersim/rcssmonitor](https://github.com/rcsoccersim/rcssmonitor)
- soccer window: [https://github.com/helios-base/soccerwindow2](https://github.com/helios-base/soccerwindow2)

#### 2. Install Python requirements

- Python version 3.11

```
pip install -r requirements.txt
```
#### 3. Installing Keepaway


Create a Virtual Environment [virtual environment](https://docs.python.org/3/tutorial/venv.html):

```shell
python3 -m venv keepaway-env
source keepaway-env/bin/activate
```

Clone and checkout the release branch

```shell
git clone https://github.com/aabayomi/keepaway-python.git
cd keepaway-python
git checkout keepaway-release
```

Install keepaway as local package

```shell
pip install -e .
```

---
## Training agents for Keepaway

#### Baseline Policy

To run and test one of the three baseline polices by [Gregory Kuhlmann and Peter Stone](https://www.cs.utexas.edu/~pstone/Papers/bib2html/b2hd-AB05.html). Follow the command below. 

All three polices can be found in the directory

```shell
keepaway/
    examples/
```

For example running the Handcoded policy 

```
cd keepaway
python3 examples/test_handcoded_agent.py
```

#### Train Custom Policy

To train a custom multi-agent policy you can edit the policies directory.
```shell
keepaway/
    examples/
```

Policies

```shell
keepaway/
    envs/
        policies/
```

#### To view the running player in the soccerwindow/rcssmonitor

``` 
ctrl + C
```

#### Viewing Logs

The gameserver logs, error and keepaway logs are in the this directory

```shell
keepaway/
    logs/
```

## Using Docker 

Build the image and run the shell script. Pass the directory to the Dockerfile as an argument

```
./build_image.sh {$DIR}
```

Run the docker image.

```
docker run -v /tmp/.X11-unix:/tmp/.X11-unix:rw -it keepaway
```
