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

if [[ $1 == "docker_build" ]]
then
    docker_build
elif [[ $1 == "docker_up" ]]
then
    docker_build
    docker_up
elif [[ $1 == "docker_test" ]]
then
    docker_build
    docker_up
    docker_test
fi
