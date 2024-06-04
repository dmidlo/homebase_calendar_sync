<!-- vscode-markdown-toc -->
	* 1. [Prerequisites](#Prerequisites)
	* 2. [Google API Setup](#GoogleAPISetup)
	* 3. [Installation](#Installation)
		* 3.1. [Using pip](#Usingpip)
		* 3.2. [From Source](#FromSource)
	* 4. [Configuration](#Configuration)
	* 5. [Running the Tool](#RunningtheTool)
		* 5.1. [Command Line](#CommandLine)
		* 5.2. [Using Docker](#UsingDocker)
* 1. [Docker Deployment Guide](#DockerDeploymentGuide)
	* 1.1. [Prerequisites](#Prerequisites-1)
	* 1.2. [Setting Up the Remote Directory](#SettingUptheRemoteDirectory)
	* 1.3. [Building and Running the Docker Container](#BuildingandRunningtheDockerContainer)
	* 1.4. [Verifying the Deployment](#VerifyingtheDeployment)
	* 1.5. [Summary](#Summary)
* 2. [Setup Guide for Developers](#SetupGuideforDevelopers)
	* 2.1. [Prerequisites](#Prerequisites-1)
	* 2.2. [Project Structure](#ProjectStructure)
	* 2.3. [Setup Script (`setup.sh`)](#SetupScriptsetup.sh)
		* 2.3.1. [Usage](#Usage)
		* 2.3.2. [Commands](#Commands)
	* 2.4. [Functions](#Functions)
	* 2.5. [Running the Tests](#RunningtheTests)
	* 2.6. [Example Workflow](#ExampleWorkflow)

```
homebase_calendar_sync --help
usage: homebase_calendar_sync [-h] [--version] [--import-secret [IMPORT_SECRET]] [--reset-remote] [--reset-db] [--reset-events]
                              [--reset-auth] [--reset-local] [--reset-all]

Homebase/Google Calendar Sync CLI

options:
  -h, --help            show this help message and exit
  --version             print package version to console.
  --import-secret [IMPORT_SECRET]
                        Path to 'client_secret.json'
  --reset-remote        Remove all homebase events from Google Calendar for current user and calendar
  --reset-db            reset the events database
  --reset-events        reset both local and remote events
  --reset-auth          reset the authentication cache
  --reset-local         reset local files and configuration
  --reset-all           reset auth config and events database
```

###  1. <a name='Prerequisites'></a>Prerequisites

Before you begin, ensure you have the following installed on your machine:

- Google API Setup
- Python 3.12 or higher
- Docker (optional, for deployment and scheduled runs via CRON)
- Git (optional, for cloning the repository)

###  2. <a name='GoogleAPISetup'></a>Google API Setup

1. **Create a New Google Developer Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project.

2. **Activate the Google Calendar API**:
   - In the Google Cloud Console, go to the API Library.
   - Search for "Google Calendar API" and enable it for your project.

3. **Create an OAuth Consent Screen**:
   - In the Google Cloud Console, navigate to "APIs & Services" > "OAuth consent screen".
   - Configure the consent screen for your project, adding necessary details like application name, support email, etc.

4. **Create OAuth 2.0 Client IDs**:
   - In the Google Cloud Console, go to "APIs & Services" > "Credentials".
   - Create credentials and select "OAuth 2.0 Client IDs".
   - Download the `client_secret.json` file and save it in your working directory.

###  3. <a name='Installation'></a>Installation

####  3.1. <a name='Usingpip'></a>Using pip

```sh
pip install homebase_calendar_sync
```

####  3.2. <a name='FromSource'></a>From Source

Alternatively, you can install the tool from the source code. Follow these steps:

1. **Clone the repository** (optional):

   ```sh
   git clone https://github.com/your-username/homebase_calendar_sync.git
   cd homebase_calendar_sync
   ```

2. **Install the dependencies**:

   ```sh
   pip install .
   ```

###  4. <a name='Configuration'></a>Configuration

Before running the tool, you need to configure it. The configuration file should include your Google API credentials and Homebase login details.

1. **Create a configuration file**:

   Create a `.env` file in your working directory with the necessary configurations.

   `touch .env`

    ***.env***
    ```sh
    CC_HOMEBASE_USERNAME = ""
    CC_HOMEBASE_PASSWORD = ""
    CC_HOMEBASE_EMPLOYEE_FIRSTNAME = ""
    CC_HOMEBASE_EMPLOYEE_LASTNAME = ""
    CC_HOMEBASE_START_DATE = "today"
    CC_HOMEBASE_END_DATE = "today"
    CC_HOMEBASE_DAYS_LOOKAHEAD = "14"
    CC_HOMEBASE_LOOKAHEAD = "True"
    CC_HOMEBASE_TIMEZONE = "America/Chicago"
    ```

###  5. <a name='RunningtheTool'></a>Running the Tool

You can run the tool in two ways: directly via command line or using Docker.

####  5.1. <a name='CommandLine'></a>Command Line

1. **Run the tool**:

   ```sh
   homebase_calendar_sync
   ```

####  5.2. <a name='UsingDocker'></a>Using Docker

* ***Developers Note:***
The included `Dockerfile` and `docker-compose.yml` are deployment versions and install via `pip install homebase`.  Docker is not used for development, use the `venv` module instead.

1. **Build the Docker image**:

   ```sh
   docker build -t homebase_calendar_sync .
   ```

2. **Run the Docker container**:

   ```sh
   docker-compose up
   ```

##  1. <a name='DockerDeploymentGuide'></a>Docker Deployment Guide

This guide provides instructions to deploy the `homebase_calendar_sync` project using Docker. Ensure you have Docker and Docker Compose installed on your machine.

###  1.1. <a name='Prerequisites-1'></a>Prerequisites

Before you begin, ensure you have the following:

- Docker and Docker Compose installed on your machine.
- Completed the Google OAuth flow on a machine with a web browser.
- `.env`, `.homebase_calendar_sync`, and `.homebase_calendar_sync_meta` files from the Google OAuth setup.

###  1.2. <a name='SettingUptheRemoteDirectory'></a>Setting Up the Remote Directory

1. **Create the working directory**:
   Create a directory on your remote machine where you will place the necessary files and run the Docker container.

   ```sh
   mkdir -p ~/homebase_calendar_sync_deployment
   cd ~/homebase_calendar_sync_deployment
   ```

2. **Transfer the necessary files**:
   Copy the `.env`, `.homebase_calendar_sync`, and `.homebase_calendar_sync_meta` files from your local machine (where you completed the Google OAuth flow) to the remote machine's working directory.

   ```sh
   scp /path/to/.env user@remote_machine:~/homebase_calendar_sync_deployment/
   scp /path/to/.homebase_calendar_sync user@remote_machine:~/homebase_calendar_sync_deployment/
   scp /path/to/.homebase_calendar_sync_meta user@remote_machine:~/homebase_calendar_sync_deployment/
   ```

3. **Verify the directory structure**:
   Ensure your working directory on the remote machine contains the necessary files:

   ```sh
   tree ~/homebase_calendar_sync_deployment
   ```

   The output should look something like this:

   ```plaintext
   ~/homebase_calendar_sync_deployment
   ├── .env
   ├── .homebase_calendar_sync
   └── .homebase_calendar_sync_meta
   ```

###  1.3. <a name='BuildingandRunningtheDockerContainer'></a>Building and Running the Docker Container

1. **Create the Dockerfile**:
   Create a `Dockerfile` in the working directory with the following content:

   ```Dockerfile
   FROM python:3.12.3-alpine

   ENV PYTHONUNBUFFERED=1

   WORKDIR /app

   RUN apk add --no-cache gcc musl-dev libffi-dev
   RUN pip install --upgrade pip
   RUN pip install --no-cache-dir homebase_calendar_sync

   CMD homebase_calendar_sync
   ```

2. **Create the docker-compose.yml file**:
   Create a `docker-compose.yml` file in the working directory with the following content:

   ```yaml
   version: '3'
   services:
     homebase_calendar_sync:
       build: .
       volumes:
         - .:/app
   ```

3. **Build the Docker image**:
   Navigate to the working directory and build the Docker image.

   ```sh
   docker-compose build
   ```

4. **Run the Docker container**:
   Start the Docker container using Docker Compose.

   ```sh
   docker-compose up
   ```

###  1.4. <a name='VerifyingtheDeployment'></a>Verifying the Deployment

Once the Docker container is running, you can verify that the `homebase_calendar_sync` tool is working correctly by checking the logs or running commands inside the container.

1. **Check the logs**:
   View the logs of the running container to ensure there are no errors.

   ```sh
   docker-compose logs -f
   ```

2. **Run commands inside the container**:
   Open a shell inside the running container to run additional commands or checks.

   ```sh
   docker-compose exec homebase_calendar_sync sh
   ```

###  1.5. <a name='Summary'></a>Summary

By following these steps, you have set up and deployed the `homebase_calendar_sync` project using Docker. Ensure your `.env`, `.homebase_calendar_sync`, and `.homebase_calendar_sync_meta` files are correctly placed in the working directory for the tool to function properly. You can now manage and synchronize your Homebase and Google Calendar events seamlessly.

##  2. <a name='SetupGuideforDevelopers'></a>Setup Guide for Developers

This guide provides instructions for developers to set up and manage the `homebase_calendar_sync` project.

###  2.1. <a name='Prerequisites-1'></a>Prerequisites

Ensure you have the following installed on your system:

- Python 3.12+
- pip (Python package installer)
- venv (optional, but recommended for creating isolated Python environments)
- Docker (if using Docker)

###  2.2. <a name='ProjectStructure'></a>Project Structure

The project structure is as follows:

```plaintext
.
├── Dockerfile
├── README.md
├── docker-compose.yml
├── events.db
├── pyproject.toml
├── setup.sh
└── src
    └── homebase_calendar_sync
        ├── __init__.py
        ├── __main__.py
        ├── config.py
        ├── db
        │   ├── __init__.py
        │   ├── __main__.py
        │   └── models.py
        ├── google_client
        │   ├── __init__.py
        │   ├── __main__.py
        │   ├── auth.py
        │   ├── drive_types.py
        │   └── google_client.py
        └── homebase_calendar_sync.py
```

###  2.3. <a name='SetupScriptsetup.sh'></a>Setup Script (`setup.sh`)

The `setup.sh` script is used for setting up the development environment, building the project, and testing deployments. Below are the different commands available in the script.

####  2.3.1. <a name='Usage'></a>Usage

Run the script with the appropriate argument to perform the desired action. For example:

```bash
./setup.sh dev
```

####  2.3.2. <a name='Commands'></a>Commands

- **`dev`**: Set up the development environment.
  
  ```bash
  ./setup.sh dev
  ```

- **`build`**: Build the project using `build` and `twine`.
  
  ```bash
  ./setup.sh build
  ```

- **`pypi`**: Build the project and upload it to PyPI.
  
  ```bash
  ./setup.sh pypi
  ```

- **`testpypi`**: Build the project and upload it to TestPyPI.
  
  ```bash
  ./setup.sh testpypi
  ```

- **`testpypi_install`**: Set up a test environment, install the project from TestPyPI, run tests, and then destroy the environment.
  
  ```bash
  ./setup.sh testpypi_install
  ```

- **`pypi_install`**: Set up a test environment, install the project from PyPI, run tests, and then destroy the environment.
  
  ```bash
  ./setup.sh pypi_install
  ```

- **`pypi_pre_docker`**: Prepare the environment for Docker, install the project from PyPI, run tests, and then destroy the environment.
  
  ```bash
  ./setup.sh pypi_pre_docker
  ```

###  2.4. <a name='Functions'></a>Functions

- **`dev`**: Uninstalls `homebase_calendar_sync`, installs necessary development dependencies, and installs the package in editable mode.
- **`build`**: Cleans the build directories, installs necessary build dependencies, and builds the project.
- **`buildenv`**: Sets up a virtual environment for testing, copies environment variables, and activates the environment.
- **`buildenv_pre_docker`**: Similar to `buildenv` but moves certain configuration files before setting up the environment.
- **`destroyenv`**: Destroys the test environment and reactivates the original environment.
- **`destroyenv_pre_docker`**: Moves back configuration files after destroying the test environment.
- **`homebase_calendar_sync_test`**: Runs a series of tests on the `homebase_calendar_sync` package to ensure it is working correctly.

###  2.5. <a name='RunningtheTests'></a>Running the Tests

The `homebase_calendar_sync_test` function is designed to test the package installation and functionality. It performs the following tests:

- Checks the help command.
- Runs the main command.
- Tests the `--reset-events` option.
- Prints the version.

To run these tests, use one of the installation commands (`testpypi_install` or `pypi_install`).

###  2.6. <a name='ExampleWorkflow'></a>Example Workflow

1. Set up the development environment:

    ```bash
    ./setup.sh dev
    ```

2. Build the project:

    ```bash
    ./setup.sh build
    ```

3. Upload to TestPyPI and install for testing:

    ```bash
    ./setup.sh testpypi_install
    ```

4. Upload to PyPI:

    ```bash
    ./setup.sh pypi
    ```

5. Prepare the environment for Docker:

    ```bash
    ./setup.sh pypi_pre_docker
    ```
