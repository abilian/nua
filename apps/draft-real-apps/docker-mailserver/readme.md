## mailserver/docker-mailserver

A fullstack but simple mail server with SMTP, IMAP, LDAP, Antispam, Antivirus, etc.

This Nua image use the 'wrap' feature:

- The build starts from an existing Docker image,
- it adds to the original docker image a basic 'nua-config' file in the /nua/metadata directory.

So the 'nua-config' file is used for metadata and 'run' information for the orchestrator, like ENV variables and providers declarations.


Build based on Docker image from:
<https://hub.docker.com/r/mailserver/docker-mailserver/tags>
version 13.2.0

Source of Dockerfile: <https://github.com/docker-mailserver/docker-mailserver/pkgs/container/docker-mailserver>.

To retrieve original Docker image:
```
docker pull mailserver/docker-mailserver:13.2.0
```
