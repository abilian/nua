Warning: use makefile, build from buld_dir

This test is designed to fail via the 'test' key:

      [build]
      pip-install = ["*.whl"]
      test = "python -c 'import non_existing_module'"

Note: we use the feature of no build.py, only a declaration of a python `wheel`
