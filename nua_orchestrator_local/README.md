# Nua orchestrator, local scripts implementation (v0 draft)

Target:

-   bootstrap service environment
-   install from local docker image and confit.toml of the app

Todo:

-   remove docker registry container:
    -   Very uneasy to manage as a service and difficult requests on it
    -   Would still need to the Nua app config
    -   So prefer local storage of image as tar file
