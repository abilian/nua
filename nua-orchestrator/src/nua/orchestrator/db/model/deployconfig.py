from sqlalchemy import JSON, TIMESTAMP, Column, Integer, String
from sqlalchemy_serializer import SerializerMixin

from .base import Base

# FUTURE = "future"
# PREVIOUS = "previous"
FAILED = "failed"
PREVIOUS = "previous"
ACTIVE = "active"
INACTIVE = "inactive"


class DeployConfig(Base, SerializerMixin):
    """The deployment configuration.

    The configuration requested from the last "nua deploy" commands, with timestamp
    and status.

    - id: system generated colum for indexes
    - state: one of "failed", "active", "inactive", "previous". "previous" is an
      inactive state fro last running config.
    - created, modified: status date
    - deploy_config: JSON data representation of deployment config, ex:
    {
        "requested": {"site":[   # original .toml request
             {
               "image": "hedgedoc:1.9.6-4",
               "domain": "test1.example.com",
               "run": {
                 "env": {
                   "CMD_DOMAIN": "test1.example.com"
                 }
               }
             },
             {
               "image": "hedgedoc:1.9.6-4",
               "domain": "test2.example.com",
               "run": {
                 "env": {
                   "CMD_DOMAIN": "test2.example.com"
                 }
               }
             }
           ]
         },
        "deployed": [
           {   # detailed configuration, 'self.sites' content
            "image": "hedgedoc:1.9.6-4",
            "domain": "test1.example.com",
            ...
          }
        ]
      }

    """

    __tablename__ = "deployconfig"

    id = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(String(16), default=INACTIVE)
    created = Column(String(40))
    modified = Column(String(40))
    deployed = Column(JSON)

    def __repr__(self):
        return (
            f"DeployConfig(state={self.state}, "
            f"created={self.created}, modified={self.modified})"
        )
