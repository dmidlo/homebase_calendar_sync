#!/bin/bash

bold=$(tput bold)
normal=$(tput sgr0)

dev()
{
    echo "${bold}pypi.sh: Setting Up Dev${normal}"
    pip uninstall -y homebase_calendar_sync
    pip install twine wheel
    pip install -e .
    echo "${bold}pypi.sh: Dev Ready.${normal}"
}

build()
{
    rm -rf ./dist ./build
    pip install build twine wheel
    python -m build
}

buildenv()
{
    echo "${bold}setting up test pip environment${normal}"
    rm -rf ../myproject
    mkdir ../myproject
    cp .env ../myproject/.env
    cd ../myproject
    pwd
    python -m venv venv
    echo "${bold}activating test pip environment${normal}"
    source venv/bin/activate
    echo "${bold}test pip environment set up complete.${normal}"
}

buildenv_pre_docker()
{
    echo "${bold}setting up test pip environment${normal}"
    rm -rf ../myproject
    mkdir ../myproject
    mv ~/.homebase_calendar_sync ../myproject/
    mv ~/.homebase_calendar_sync_meta ../myproject/
    cp .env ../myproject/.env
    cd ../myproject
    pwd
    python -m venv venv
    echo "${bold}activating test pip environment${normal}"
    source venv/bin/activate
    echo "${bold}test pip environment set up complete.${normal}"
}

destroyenv()
{
    cd ../homebase_calendar_sync
    rm -rf ../myproject
    echo "${bold}leaving test pip environment${normal}"
    source venv/bin/activate
}

destroyenv_pre_docker()
{
    mv .homebase_calendar_sync ~/
    mv .homebase_calendar_sync_meta ~/
    cd ../homebase_calendar_sync
    rm -rf ../myproject
    echo "${bold}leaving test pip environment${normal}"
    source venv/bin/activate
}

homebase_calendar_sync_test()
{
    echo "${bold}testing homebase_calendar_sync --help test pip environment${normal}"
    homebase_calendar_sync --help
    echo "${bold}testing homebase_calendar_sync test pip environment${normal}"
    homebase_calendar_sync
    echo "${bold}testing homebase_calendar_sync --reset-events test pip environment${normal}"
    homebase_calendar_sync --reset-events
    echo "${bold}printing version to test pip environment${normal}"
    homebase_calendar_sync --version
}

docker_build()
{
    echo "${bold}Building docker image...${normal}"
    docker-compose down
    docker-compose build --no-cache
}

docker_up()
{
    echo "${bold}Bringing up container with docker-compose...${normal}"
    docker-compose down
    docker-compose up -d
    docker-compose ps
}

docker_test()
{
    echo "${bold}testing homebase_calendar_sync --help test pip environment from docker${normal}"
    docker-compose exec app homebase_calendar_sync --help
    echo "${bold}testing homebase_calendar_sync test pip environment from docker${normal}"
    docker-compose exec app homebase_calendar_sync
    echo "${bold}testing homebase_calendar_sync --reset-events test pip environment from docker${normal}"
    docker-compose exec app homebase_calendar_sync --reset-events
    echo "${bold}printing version to test pip environment from docker from docker${normal}"
    docker-compose exec app homebase_calendar_sync --version

    docker-compose down
}

if [[ $1 == "dev" ]]
then
    dev
    exit 0
elif [[ $1 == "build" ]]
then
    build
    exit 0
elif [[ $1 == "pypi" ]]
then
    build
    twine upload -r pypi --config-file .pypirc dist/*
    exit 0
elif [[ $1 == "testpypi" ]]
then
    build
    twine upload -r testpypi --config-file .pypirc dist/*
elif [[ $1 == "testpypi_install" ]]
then
    buildenv
    echo "${bold}installing homebase_calendar_sync from testpypi: https://test.pypi.org/simple/${normal}"
    python3 -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ homebase_calendar_sync
    homebase_calendar_sync_test
    destroyenv
elif [[ $1 == "pypi_install" ]]
then
    buildenv
    echo "${bold}installing homebase_calendar_sync from pypi: https://pypi.org/${normal}"
    pip install homebase_calendar_sync
    homebase_calendar_sync_test
    destroyenv
elif [[ $1 == "pypi_pre_docker" ]]
then
    buildenv_pre_docker
    echo "${bold}installing homebase_calendar_sync from pypi: https://pypi.org/${normal}"
    pip install homebase_calendar_sync
    homebase_calendar_sync_test
    destroyenv_pre_docker
elif [[ $1 == "docker_build" ]]
then
    docker_build
elif [[ $1 == "docker_test" ]]
then
    docker_build
    docker_up
    docker_test
fi
