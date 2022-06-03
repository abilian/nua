ARG nua_version
FROM nua_base:${nua_version}

# app build:
ADD nua-config.toml /nua/build/
RUN nuad setup_app /nua/build

# debug
RUN nuad --help

#
# Configure and start
#
##ADD start.py /nua/scripts/

CMD ["/nua/scripts/start.py"]
