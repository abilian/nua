ARG nua_builder_tag
FROM ${nua_builder_tag} AS compile-image

RUN apt-get install -y build-essential git
RUN python -m pip install poetry && cd /nua/nua_build && poetry install --no-dev && nua_build_self_setup

FROM ${nua_builder_tag} AS runtime-image
COPY --from=compile-image /nua /nua

# app build:
COPY . /nua/build
RUN nua_build_setup_app


ARG nua_expose
EXPOSE ${nua_expose}
CMD ["python", "/nua/scripts/start.py"]
