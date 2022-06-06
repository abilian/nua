ARG nua_base_version
FROM ${nua_base_version}

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
