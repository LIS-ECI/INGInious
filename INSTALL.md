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

First, you need to install the ECINGInious frontend (read the **Note** section below):

```
inginious-install webapp-contest
```
This will help you create the configuration file in the current directory.

**Important notes while running previous command:**

 - Don't use minified javascript by the moment.
 - Install the **python3pylint** container.

Then, go to your **storage folder** (previously defined in the configuration wizard) and copy the provided **run** folder (resources folder) into it.

### Enabling plugins (optional)

#### Plagiarism check plugin

Edit your configuration file and add the following lines in the *plugins* section:

```
-   name: Plagiarism Checker
    plugin_module: inginious.frontend.webapp_contest.plugins.plagiarism
```

Then, go to your **storage folder** (previously defined in the configuration wizard) and copy the provided **plagiarism** folder (resources folder) into it.

#### ECI authentication method plugin

Edit your configuration file and add the following lines in the *plugins* section:

```
-   name: DB Auth
    plugin_module: inginious.frontend.webapp_contest.plugins.auth.eci_auth
```

### Configuring additional parameters (optional)

#### web_debug

Enable or disable the web.py developer debugger (for non-production servers only).

```
web_debug: True
```

## Running ECINGInious

To run the frontend, please use:

```
inginious-webapp-contest --conf CONF_FILE_PATH --host HOST --port PORT
```
This will open a small Python web server and display the url on which it is bind in the console.
