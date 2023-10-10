from .build import BuildStage
from .deploy import DeployStage
from .install import InstallStage
from .prepare import PrepareStage

STAGE_CLASSES = {
    "prepare": PrepareStage,
    "install": InstallStage,
    "build": BuildStage,
    "deploy": DeployStage,
}
