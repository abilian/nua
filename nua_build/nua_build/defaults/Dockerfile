ARG nua_base_version
FROM ${nua_base_version} AS compile-image

RUN apt-get install -y build-essential git
RUN python -m pip install poetry && cd /nua/nua_build && poetry install --no-dev && nuad setup_nua

FROM ${nua_base_version} AS runtime-image
COPY --from=compile-image /nua /nua

# app build:
COPY . /nua/build
RUN nuad setup_app /nua/build


ARG nua_expose
EXPOSE ${nua_expose}
CMD ["python", "/nua/scripts/start.py"]
