Example unsing Flask, SQLAlchemy on sqlite, Docker bind volume.


Note:
- we use the feature of no build.py but project auto detection
- using "bind" volume in /var/tmp : may fail on some tests is file exist and test is
  run with anoter user.
