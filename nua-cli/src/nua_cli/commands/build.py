# @cli.command()
# def build(
#     path: str = ".",
#     experimental: bool = typer.Option(
#         False, "--experimental", "-x", help="Use experimental builder (from nua-dev)."
#     ),
#     verbose: int = typer.Option(
#         0, "--verbose", "-v", help="Increase verbosity level, until -vv. ", count=True
#     ),
#     quiet: int = typer.Option(
#         0, "--quiet", "-q", help="Decrease verbosity level", count=True
#     ),
# ):
#     """Build app but don't deploy it."""
#
#     verbosity = 1 + verbose - quiet
#     verbosity_flags = verbosity * ["-v"]
#
#     if experimental:
#         typer.secho(
#             "Using experimental builder (from nua-dev).", fg=typer.colors.YELLOW
#         )
#         subprocess.run(["nua-dev", "build", path])
#     else:
#         subprocess.run(["nua-build"] + verbosity_flags + [path])
#
