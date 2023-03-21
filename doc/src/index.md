# Nua Documentation


!!! danger "Do not use yet (in production)!"
    This code is still experimental, and not meant for public consumption.

    We plan to have a first usable release, by the end of Q1 2023, and a stable release by the end of Q2 2023.

    You can accelerate this process by [funding](./funding/) the project.


## What is Nua?

Nua is an open source, self-hosted cloud platform project (a *PaaS* - *platform as a service*). More than just a technical platform, it aims to cover the entire life cycle of web applications, from development (and packaging) to deployment and maintenance, including security.

It is particularly aimed at organisations (SMEs, associations, public services, etc.) that wish, or need, to implement a digital autonomy strategy, and as such are moving towards open source software as a priority.


## Vision

The Nua project was born out of a double need within Abilian:

- To use the best of open source software for its internal needs: development tools (*bug-tracker*, continuous integration...), communication and collaboration tools (Wiki, web office, messaging, video...), management tools (invoicing, ERP, HR...), marketing tools (websites, newsletters...), etc. With the constraints specific to an SME: simplify deployment and integration, minimise hosting costs and the effort devoted to maintenance and version upgrades, ensure maintenance in operational conditions, in particular security and resilience in the face of hardware and network hazards.
- To make available to its clients and prospects, in SaaS mode, both applications developed by the company and third-party applications, integrated according to their needs, taking into account the same constraints as above.

With its long experience in Linux system administration, software packaging for Linux distributions, Docker and the main PaaS solutions on the market, the Nua development team set out two years ago to rationalise the tools and methodologies developed, tested or used internally to make an open source product that would meet the needs of developers to easily deploy, in test, demo or production mode, one or more instances of applications, whether developed internally or by third parties.

This vision is based on a set of principles:

- Favour, as much as possible, **declarative configuration** rather than imperative, and **conventions** rather than explicit configuration, avoiding duplication of information.
- Rely, when they exist, on proven technologies that are already widely used: the Python language, the **Open Container Initiative** (OCI) standards, the Docker platform (without, however, ignoring other isolation and orchestration technologies that may be relevant for certain uses).
- Aligning development methods and the developer experience with the *best practices* of the PaaS market, in particular the "***12 factor apps***" philosophy. Make the deployment of applications based on the main web frameworks on the market (Django, Rails, Laravel, etc.) as easy as possible.
- To secure the whole **software supply chain** by applying current or emerging practices, notably the notion of "SBOM" (*software bill of material*).
- Directly cover current needs, while making the platform **extensible** (through plugins) to allow the use of emerging or more confidential technologies.


## Presentation

### High-level / strategic presentation, given in 2022 and 2023

<iframe class="speakerdeck-iframe" style="border: 0px none; background: rgba(0, 0, 0, 0.1) padding-box; margin: 0px; padding: 0px; border-radius: 6px; box-shadow: rgba(0, 0, 0, 0.2) 0px 5px 40px; width: 100%; height: auto; aspect-ratio: 560 / 314;" src="https://speakerdeck.com/player/f7a0c4f8df0a49be8d6d5e944a0eed90" title="Nua - a self-hosted, resilient PaaS" allowfullscreen="true" mozallowfullscreen="true" webkitallowfullscreen="true" data-ratio="1.78343949044586" frameborder="0"></iframe>

### Python-focused presentation (given at PyConFr 2023 in Bordeaux)


<iframe class="speakerdeck-iframe" style="border: 0px none; background: rgba(0, 0, 0, 0.1) padding-box; margin: 0px; padding: 0px; border-radius: 6px; box-shadow: rgba(0, 0, 0, 0.2) 0px 5px 40px; width: 100%; height: auto; aspect-ratio: 560 / 314;" src="https://speakerdeck.com/player/b69f33062ebb48a3b884b7b2bc5f0a4a" title="Nua, un PaaS open source en Python pour l'auto-hébergement de vos applications" allowfullscreen="true" data-ratio="1.78343949044586" frameborder="0"></iframe>

### Presenation at IMPULSE 2023 (1 slide, in French)

<iframe class="speakerdeck-iframe" style="border: 0px none; background: rgba(0, 0, 0, 0.1) padding-box; margin: 0px; padding: 0px; border-radius: 6px; box-shadow: rgba(0, 0, 0, 0.2) 0px 5px 40px; width: 100%; height: auto; aspect-ratio: 560 / 314;" src="https://speakerdeck.com/player/d36daeb62d4347ad8b96fa63e649b6c8" title="Pitch Abilian @ IMPULSE 2023" allowfullscreen="true" data-ratio="1.78343949044586" frameborder="0"></iframe>


## Concept Map

<img src="diagrams/mindmaps/Nua Concept Map.png">


## Use cases

<img src="diagrams/others/Nua use cases.png">


## Read the documentation

- [User documentation](./user/)

- [Developer documentation](./dev/)


## Current status and outlook

Nua is open source, under active development at <https://github.com/abilian/nua>.

Nua has been used internally at Abilian for several months to host non-critical applications, and a first beta version was released in February 2023.

The project will continue to grow over the coming months and years, including:

- the creation of a catalogue of applications;
- the creation of a web interface for managing the orchestrator, which will be aimed at users less comfortable with the command line interface currently available;
- support for more build tools and profiles, runtime environments, services;
- the integration, upstream and downstream, of more security-related tools, such as vulnerability scanners, firewalls, centralized authentication.

Nua is an ambitious project, we are confident that it will meet concrete needs beyond our own: we are listening to the remarks and comments of the free software community.
