import os

from nua.lib.exec import exec_as_nua

exec_as_nua(
    "bundle exec rails s",
    cwd="/nua/build/webauthn-rails-demo-app",
    env=os.environ,
)
