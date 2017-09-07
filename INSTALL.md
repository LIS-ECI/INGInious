# Installation

ECINGInious is intended to run on Linux (kernel 3.10+).

## Dependencies setup

ECINGInious needs:

- Python (with pip) 3.5+
- Docker 1.12+
- MongoDB
- Libtidy
- LibZMQ

### Ubuntu 16.04+

First, we need to install docker:
```
sudo apt-get install -y docker docker-compose
```

Add the current user to the docker group in order to use ECINGInious as non-root user:

```
groupadd docker
gpasswd -a $USER docker
newgrp docker
```

Install required dependencies:

```
sudo apt-get install git mongodb gcc tidy python3 python3-pip python3-dev libzmq-dev
```

You can now start and enable the mongod and docker services:

```
# systemctl start mongodb
# systemctl enable mongodb
# systemctl start docker
# systemctl enable docker
```

## Installing ECINGInious

The recommended setup is to install ECINGInious via pip and the master branch of the ECINGInious git repository.

```
pip3 install --upgrade git+https://github.com/LIS-ECI/INGInious.git
```

## Configuring ECINGInious

First, you need to install the ECINGInious frontend:

```
inginious-install webapp-contest
```
This will help you create the configuration file in the current directory

## Running ECINGInious

To run the frontend, please use:

```
inginious-webapp --conf CONF_FILE_PATH --host HOST --port PORT
```
This will open a small Python web server and display the url on which it is bind in the console.