ARG nua_base_version
FROM ${nua_base_version}

# app build:
COPY . /nua/build
RUN nuad setup_app /nua/build

CMD ["python", "/nua/scripts/start.py"]
