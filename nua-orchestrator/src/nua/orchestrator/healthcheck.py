from copy import deepcopy
from typing import Any

HEALTHCHECK_DEFAULT = {
    "command": "",
    "start_period": 120,
    "interval": 5,
    "timeout": 30,
    "retries": 3,
}


class HealthCheck:
    def __init__(self, conf: dict):
        if not conf:
            self._dict = {}
            return
        self._dict = deepcopy(HEALTHCHECK_DEFAULT)
        self._parse_cmd(conf)
        self._parse_start_period(conf)
        self._parse_interval(conf)
        self._parse_timeout(conf)
        self._parse_retries(conf)

    def _parse_cmd(self, conf: dict):
        if "command" in conf:
            cmd = conf["command"]
        elif "cmd" in conf:
            cmd = conf["cmd"]
        else:
            return
        self._dict["command"] = str(cmd).strip()

    def _parse_start_period(self, conf: dict):
        if "start-period" in conf:
            period = conf["start-period"]
        elif "start_period" in conf:
            period = conf["start_period"]
        else:
            return
        self._dict["start-period"] = self.force_int(period)

    def _parse_interval(self, conf: dict):
        if "interval" in conf:
            self._dict["interval"] = self.force_int(conf["interval"])

    def _parse_timeout(self, conf: dict):
        if "timeout" in conf:
            self._dict["timeout"] = self.force_int(conf["timeout"])

    def _parse_retries(self, conf: dict):
        if "retries" in conf:
            self._dict["retries"] = self.force_int(conf["retries"])

    @staticmethod
    def force_int(value: Any) -> int:
        if not value:
            return 0
        try:
            return max(0, int(value))
        except ValueError:
            return 0

    @staticmethod
    def second_to_nano(sec: Any) -> int:
        if not sec:
            return 0
        try:
            nano = int(float(sec) * 10**9)
            if nano < 10**6:
                nano = 0
            return nano
        except ValueError:
            return 0

    def as_dict(self) -> dict:
        return self._dict

    def as_docker_params(self) -> dict:
        params: dict[str, Any] = {}
        if not self._dict["command"]:
            return params
        # expecting a str -> the command wil be used as CMD-SHELL by py-docker:
        params["test"] = self._dict["command"]
        params["start_period"] = self.second_to_nano(self._dict["start-period"])
        params["interval"] = self.second_to_nano(self._dict["interval"])
        params["timeout"] = self.second_to_nano(self._dict["timeout"])
        params["retries"] = self._dict["retries"]
        return params
