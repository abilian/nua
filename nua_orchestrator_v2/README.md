# Nua demos

Empty from actual demos at the moment.

-   `demo_orchestrator_zmq.py` : basic testing of the RPC protocols.


## Installation and test:

    cd ../nua_cli
    poetry install
    cd ../nua_orchestrator
    poetry install
    python -c 'import nua_orchestrator as o; o.restart()'
    cd ../demos
    python demo_orchestrator_zmq.py
