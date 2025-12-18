# Windows Setup (Locally)

## Intro 

This explains how to locally run VulcanLab locally on Windows. You may want to run it locally if:

* You're helping out with development
* You already have a Postgres DB running (with pgvector) and want to use that
* You want to play around with the source for whatever reason (optimizations or if you can't get the docker version running and you need to install some specific libraries or something in the virtual python environment) 

**Note:** If you just want to get up and running on windows (or any other OS) I recommend you just get the [docker installation](./docker_setup.md) going.

## Windows WSL Installation

I now exclusively run VulcanLab in Windows WSL (Windows Subsystem for Linux) so it's highly recommended to run it locally this way:

* Cursor, Claude, and Antigravity (probably Codex too) run much better in Linux than Windows
* All the latest tests and python files are optimized for Linux 

## Step 1 : Install WSL in Windows

Ideally install Ubuntu 24.xx -- that is what I'm running. Older versions of Ubuntu like 18, might give you trouble because it supports older versions of Python. 

Follow the official instructions [here](https://learn.microsoft.com/en-us/windows/wsl/install)

## Step 2: Install Pre-requisites in WSL

1. Python 3.10 or higher

* Ubuntu 24.04 defaults to Python 3.12, which is perfect for our use case. You probably don't need to anything here other than possibly aliasing `python3` to `python` (you probably don't need to do this, but it's recommended).
* Handy package for the aliasing (so you don't have to mess with `.bashrc` or `.zhrc` files): `sudo apt install python-is-python3`
* Check the version of `python` to ensure it's 3.10+: `python --version`

2. Pip and Venv

* Ubuntu/Linux might not ship with python3-pip and python3-venv (some dev versions might?)
* `sudo apt install python3-pip python3-venv`

2. Node/npm - ideally with npx

