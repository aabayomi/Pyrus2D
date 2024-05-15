# Keepaway-Python


This project offers a python implementation of the RoboCup keepaway environment, designed for deep reinforcement learning research. The environment is based on the [CYRUS](https://arxiv.org/abs/2211.08585) Python based RoboCup 2D soccer simulator, enabling researchers and developers to test and develop multi-agent reinforcement learning algorithms.

The published [paper](https://www.cs.utexas.edu/~pstone/Papers/bib2html/b2hd-AB05.html) and [code](https://github.com/tjpalmer/keepaway) outlines the motivation for keepaway for reinforcement learning and some initial research results using the environment.


To get started with this project, follow the instructions in the [Quick Start Guide](https://github.com/aabayomi/keepaway-python#quick-start).

### Using Docker

This is the recommended way to avoid incompatible package versions. Instructions are available [here](doc/docker.md).



<!-- * [RoboCup ](https://www.robocup.org/) [Soccer Simulation 2D League](https://rcsoccersim.github.io/) 2D simulation League
* [Server documentation](https://rcsoccersim.readthedocs.io/) RCSSServer Documentation -->

---
## Quick Start Guide

### On your computer

#### 1. Install required dependencies 
#### Linux

This code has only been tested on Ubuntu 20.04, which rcssserver and rcssmonitor is supported.

Install rcssserver and rcssmonitor (soccer window for debugging proposes)

- rcssserver: [https://github.com/rcsoccersim/rcssserver](https://github.com/rcsoccersim/rcssserver)
- rcssmonitor: [https://github.com/rcsoccersim/rcssmonitor](https://github.com/rcsoccersim/rcssmonitor)
- soccer window: [https://github.com/helios-base/soccerwindow2](https://github.com/helios-base/soccerwindow2)

#### 2. Install Python requirements

- Python version 3.11

```
pip install -r requirements.txt
```

#### 3. Installing keepaway


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
#### 4. Run baseline policy 
```shell
python3 -m examples.test_random_agent
```


## Training agents for keepaway

<!-- #### Baseline Policy

To run and test one of the three baseline polices by [Gregory Kuhlmann and Peter Stone](https://www.cs.utexas.edu/~pstone/Papers/bib2html/b2hd-AB05.html). Follow the command below. 

All three polices can be found in the directory -->

<!-- ```shell
keepaway/
    examples/
``` -->

<!-- For example running the Handcoded policy  -->

<!-- ```
cd keepaway
python3 examples/test_handcoded_agent.py
``` -->

<!-- #### Train Custom Policy -->

<!-- To train a custom multi-agent policy you can edit the policies directory.
```shell
keepaway/
    examples/
``` -->

<!-- Policies

```shell
keepaway/
    envs/
        policies/
``` -->

<!-- #### To view the running player in the soccerwindow/rcssmonitor

``` 
ctrl + C
```

#### Viewing Logs

The gameserver logs, error and keepaway logs are in the this directory

```shell
keepaway/
    logs/
``` -->
