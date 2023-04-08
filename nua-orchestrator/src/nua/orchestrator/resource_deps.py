"""Solve the order of evaluation of resources dynamic parameters."""
from nua.lib.panic import Abort

from .resource import Resource


class Task:
    def __init__(self, resource: Resource):
        self.name = resource.resource_name
        self.dependencies = set()
        self.resource = resource
        for variable in resource.env.values():
            if not isinstance(variable, dict):
                continue
            dep = variable.get("from", "")
            if not dep:
                continue
            self.dependencies.add(dep)


class ResourceDeps:
    """Solve the order of evaluation of resources dynamic parameters.

    Raise on circular dependencies.
    """

    def __init__(self):
        self.nodes = []
        self.node_names = set()
        self.ordered_resources = []

    def add_resource(self, resource: Resource):
        task = Task(resource)
        if task.name in self.node_names:
            raise Abort(f"Duplicate name in resources: {task.name}")

        self.node_names.add(task.name)
        self.nodes.append(task)

    def solve(self) -> list:
        while self.nodes:
            self.solve_step()
        return self.ordered_resources[:]

    def solve_step(self):
        free = [task for task in self.nodes if not task.dependencies]
        if not free:
            names = [task.name for task in self.nodes]
            raise Abort(f"Circular dependencies in resources: {names}")

        self.ordered_resources.extend([task.resource for task in free])
        self.nodes = [task for task in self.nodes if task not in free]
        free_names = {task.name for task in free}
        for task in self.nodes:
            task.dependencies = task.dependencies.difference(free_names)
