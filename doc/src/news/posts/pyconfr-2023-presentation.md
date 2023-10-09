---
date: 2023-03-22
description: We gave a talk about Nua during PyConFR 2023 in Bordeaux.
categories:
  - talk
  - slides
  - conference
---

# Nua talk at PyConFR 2023

## Context

Organised by AFPy, the French Python User Association, [this conference](https://www.pycon.fr/) is free, entirely run by volunteers and dedicated to bringing together people interested in the Python programming language.


## Slides

### French version

<iframe class="speakerdeck-iframe" style="border: 0px none; background: rgba(0, 0, 0, 0.1) padding-box; margin: 0px; padding: 0px; border-radius: 6px; box-shadow: rgba(0, 0, 0, 0.2) 0px 5px 40px; width: 100%; height: auto; aspect-ratio: 560 / 314;" src="https://speakerdeck.com/player/b69f33062ebb48a3b884b7b2bc5f0a4a" title="Nua, un PaaS open source en Python pour l'auto-hébergement de vos applications" allowfullscreen="true" data-ratio="1.78343949044586" frameborder="0"></iframe>


### English version

<iframe class="speakerdeck-iframe" style="border: 0px none; background: rgba(0, 0, 0, 0.1) padding-box; margin: 0px; padding: 0px; border-radius: 6px; box-shadow: rgba(0, 0, 0, 0.2) 0px 5px 40px; width: 100%; height: auto; aspect-ratio: 560 / 314;" src="https://speakerdeck.com/player/1aba6986409649189d623ce3dd150bbd" title="Nua, an open source PaaS in Python to self-host your applications" allowfullscreen="true" data-ratio="1.78343949044586" frameborder="0"></iframe>

(This is a translation of the slides that were presented during the conference.)

## Summary

Nua is an open source cloud platform project launched by Abilian in 2021. It offers a PaaS (platform as a service) that can be easily installed on bare metal or virtualised servers, and which allows containerised web applications to be run, managing their lifecycle, the providers they need (storage, databases, etc.), user access rights, backups, monitoring, logs, etc.

Nua enables the management of applications from an application portfolio ("marketplace"), i.e. packaged and optimised by the platform's developers (or third parties). Nua also allows the deployment of applications under development (demo / qualif / prod), including several instances of the same application, and including automatic deployment (example use case: create demo instances on request from prospects, optimising provider consumption).

Nua is based on the main standards of the open source and cloud world: database (Postgres, MySQL, MongoDB, Redis), storage (S3), OCI, dockerfiles and buildpacks, LDAP and SSO, etc. Nua currently relies on Docker, but will eventually allow applications to be deployed in other execution environments (other containers, classic or lightweight VMs, SlapOS...).

Documentation and source code:

- https://nua.rocks
- https://github.com/abilian/nua


## Presentation outline

- Vision and main features of the project

    - Simplification of packaging and multi-instance deployment,
    - Self-hosting, digital sovereignty
    - General architecture

- Why python?

    - A python runtime in the container
    - An orchestrator driving the containers
    - Reuse of components between packaging, script execution and orchestration

- Examples and demo

    - Configuration file (packager view)
    - Deploying configurations (user CLI view)

- Roadmap and how to contribute

## Take-aways

- For developers / devops: how Nua can help to quickly deploy dev versions in the dev / preprod / prod phase, and to manage production constraints (backup, upgrades)?
- For IT managers: how can Nua help to easily deploy and manage a portfolio of open source Web applications (intranet / extranet / Web)?
- For third-party application developers: how to port their applications to Nua?
- For open source contributors: what is Nua's roadmap and how to contribute to it?
