# Keepaway Python Implementation

## RoboCup Soccer Simulation 2D Python Base Code


This implementation is based on [CYRUS](https://arxiv.org/abs/2211.08585) soccer simulation 2D team PYRUS2D fork.
Keepaway an originally designed in UT Austin by [Gregory Kuhlmann and Peter Stone](https://www.cs.utexas.edu/~pstone/Papers/bib2html/b2hd-AB05.html).

This package contains a python implementation of the original [c++ version](https://github.com/tjpalmer/keepaway), integrated with Open AI gym suitable for 
multi-agent deep reinforcement learning. The framework includes all low- and mid-level keepaway behaviors. However, the framework was designed to make it easy to insert your own learning code for deep reinforcement learning.

The main implementation of keepaway is in ``` utils/ ```

```shell
keepaway/
    utils/
```

---
## Quick Start 

### On Linux

#### 1. Install required simulator dependencies 

This code has only been tested on Linux, the rcssserver and rcssmonitor only support Linux/Ubuntu.

Install rcssserver and rcssmonitor (soccer window for debugging proposes)

- rcssserver: [https://github.com/rcsoccersim/rcssserver](https://github.com/rcsoccersim/rcssserver)
- rcssmonitor: [https://github.com/rcsoccersim/rcssmonitor](https://github.com/rcsoccersim/rcssmonitor)
- soccer window: [https://github.com/helios-base/soccerwindow2](https://github.com/helios-base/soccerwindow2)

#### 2. Install Python requirements

- Python v3.11
- coloredlogs==15.0.1
- pyrusgeom==0.1.2
- scipy==1.10.1

```
pip install -r requirements.txt
```
#### 3. Installing Keepaway


Create a Virtual Environment [virtual environment](https://docs.python.org/3/tutorial/venv.html):

```shell
python3 -m venv keepaway-env
source keepaway-env-env/bin/activate
```

Clone and checkout the release branch

```shell
git clone https://github.com/aabayomi/Pyrus2D.git
cd Pyrus2D
git checkout keepaway-release
```

---
## Training agents for Keepaway

#### Baseline Policy

To run and test one three baseline polices by [Gregory Kuhlmann and Peter Stone](https://www.cs.utexas.edu/~pstone/Papers/bib2html/b2hd-AB05.html). Follow the command below. 

All three polices can be found in the directory

```shell
keepaway/
    examples/
```

For example running the Handcoded policy 

```
cd keepaway/examples
python3 test_handcoded_agent.py
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



## Useful links

- CYRUS team: [https://cyrus2d.com/](https://cyrus2d.com/)
- RoboCup: [https://www.robocup.org/](https://www.robocup.org/)
- Soccer Simulation 2D League: [https://rcsoccersim.github.io/](https://rcsoccersim.github.io/)
- Server documentation: [https://rcsoccersim.readthedocs.io/](https://rcsoccersim.readthedocs.io/)
