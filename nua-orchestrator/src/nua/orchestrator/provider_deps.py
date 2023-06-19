"""Solve the order of evaluation of providers dynamic parameters."""
from nua.lib.panic import Abort

from .provider import Provider


class Task:
    def __init__(self, provider: Provider):
        self.name = provider.provider_name
        self.dependencies = set()
        self.provider = provider

        volume_names = {volume.get("name", "") for volume in provider.volumes}
        for variable in provider.env.values():
            if not isinstance(variable, dict):
                continue
            dep = variable.get("from", "")
            if not dep:
                continue
            if dep in volume_names:
                continue
            self.dependencies.add(dep)


class ProviderDeps:
    """Solve the order of evaluation of providers dynamic parameters.

    Raise on circular dependencies.
    """

    def __init__(self):
        self.nodes = []
        self.node_names = set()
        self.ordered_providers = []
        self.volumes_names = set()

    def add_provider(self, provider: Provider):
        task = Task(provider)
        if task.name in self.node_names:
            raise Abort(f"Duplicate name in providers: {task.name}")

        self.node_names.add(task.name)
        self.nodes.append(task)

    def solve(self) -> list:
        while self.nodes:
            self.solve_step()
        return self.ordered_providers[:]

    def solve_step(self):
        free = [task for task in self.nodes if not task.dependencies]
        if not free:
            names = [task.name for task in self.nodes]
            raise Abort(f"Circular dependencies in providers: {names}")

        self.ordered_providers.extend([task.provider for task in free])
        self.nodes = [task for task in self.nodes if task not in free]
        free_names = {task.name for task in free}
        for task in self.nodes:
            task.dependencies = task.dependencies.difference(free_names)
