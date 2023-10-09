## Dolibarr wrap version

Use the 'wrap' build feature:

- start from an existing Docker image
- add the 'nua-config' file in the /nua/metadata directory

So the 'nua-config' file is use for metadata and 'run' information for the orchestrator, like ENV variables and providers declaration


Build based on Docker image from:
<https://hub.docker.com/r/tuxgasy/dolibarr/>
version 16.0.4

Source of Dockerfile: <https://github.com/tuxgasy/docker-dolibarr>.

To retrieve original Docker image:
```
docker pull tuxgasy/dolibarr:16.0.4
```
