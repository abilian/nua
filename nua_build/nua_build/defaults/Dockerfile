ARG nua_base_version
FROM ${nua_base_version}

# app build:
COPY . /nua/build
RUN nuad setup_app /nua/build

ARG nua_expose
EXPOSE ${nua_expose}
CMD ["python", "/nua/scripts/start.py"]
