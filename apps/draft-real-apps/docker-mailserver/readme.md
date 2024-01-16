## Image mailserver/docker-mailserver

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

## Configure & deploy

Most configuration options of the docker-mailserver are available through the Nua deployment configuration. The full list of options is in the [env] tag of the `nua-config.toml` file.

As an example of configuration see the file `sample_deploy.json`:

- The mail is configured for the domain "mail.example.com"
- With email and password address for the postmaster at "example.com"


```json
{
    "site": [
        {
            "label": "mail",
            "image": "docker-mailserver",
            "domain": "mail.example.com",
            "env": {
                "POSTMASTER_ADDRESS": "postmaster@example.com",
                "POSTMASTER_PASSWD": "some_passwd",
                "OVERRIDE_HOSTNAME": "mail.example.com"
            }
        }
    ]
}
```

With this basic config, the mail server will accept mail from the local host on port 25 (without ssl), then send it with DKIM signature.

When deploying the docker-mail server, a `Letsencrypt` certificate is automatically requested, and a DKIM key is generated.
3 additional configuration files are written in the `/home/nua/letsencrypt` folder to help to the mail configuration on the domain DNS declaration (with "example.com" replaced by the actual domain name):

- `example.com_spf.txt`: a medium strength SPF string (feel free to adapt).
- `example.com_dmarc.txt`: a medium strength DMARC string (feel free to adapt).
- `example.com_dkim.pub`: the DKIM public key of this mail server.
