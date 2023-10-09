## mailserver/docker-mailserver

A fullstack but simple mail server with SMTP, IMAP, LDAP, Antispam, Antivirus, etc.

Use the 'wrap' build feature:

- start from an existing Docker image
- add the 'nua-config' file in the /nua/metadata directory

So the 'nua-config' file is use for metadata and 'run' information for the orchestrator, like ENV variables and providers declaration


Build based on Docker image from:
<https://hub.docker.com/r/mailserver/docker-mailserver/tags>
version 12.1.0

Source of Dockerfile: <https://github.com/docker-mailserver/docker-mailserver/pkgs/container/docker-mailserver>.

To retrieve original Docker image:
```
docker pull mailserver/docker-mailserver:12.1.0
```
