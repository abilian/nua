# Nua orchestrator, local scripts implementation (v0 draft)

Target:

-   bootstrap service environment
-   install from local docker image and confit.toml of the app

Todo:

-   remove docker registry container:
    -   Very uneasy to manage as a service and difficult requests on it
    -   Would still need to the Nua app config
    -   So prefer local storage of image as tar file


## using docker image for postgres

docker pull postgres:14.5
docker run --name nua-postgres -e POSTGRES_PASSWORD=xxxpwd -d postgres:14.5


"depends_on" -> use nua "service" ?
