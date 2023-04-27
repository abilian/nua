# Nua Architecture

## C4 Diagrams

### Context diagram (level 1)

![Level 1](../diagrams/c4/level1.png)

### Container diagrams (level 2)

![Level 2](../diagrams/c4/level2.png)


## Components

The main components are:

- The [builder](./builder/)
- The [orchestrator](./orchestrator/)

## Sub-project structure

The Nua project is (currently) structured as as a monorepo with several sub-projects.

The subprojects are structured as follows:

- `nua-lib`: common code shared by all subprojects.
- `nua-agent`: the build agent that runs in the build container.
- `nua-build`: the [builder](./builder/) that orchestrates the build.
- `nua-orchestrator`: the [orchestrator](./orchestrator/).
- `nua-server`: the web UI.

The dependencies between the subprojects are as follows:

- `nua-lib` doesn't depend on any other subproject.
- `nua-agent` should depends only on `nua-lib`.
- `nua-build` should depends only on `nua-lib`.
- `nua-orchestrator` should depends only on `nua-lib`.
- `nua-server` doesn't depend on any other subproject (could depend on `nua-lib`). Also could be merged with `nua-orchestrator` someday.
- `nua-cli` doesn't depend on any other subproject (could depend on `nua-lib`).
