Packaged apps
=============

First approach of files and configuration for packaging.  Just a very few apps at the moment, since thre the objective is to try the config scheme.


A "nua-config.toml" will contain required information for building the app.

So the idea is as follows when we run some `nua build` command:

1) `nua build` examines the contents of the `nua-config.toml` file (there is always one). If a build method is specified, apply it, otherwise guess based on package contents.

2) `nua build` will generate a `Dockerfile` by default (unless we decided to create our own Docker configuration, in which case `nua build` will just launch `docker`. At the limit, we could omit Nua Fall. )

3) The generated "Dockerfile" uses Python scripts located in the "runtime". These scripts also have access to `nua-config.toml`. Control of action can be described in a declarative manner.
