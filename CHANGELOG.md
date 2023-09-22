# Changelog

All notable changes to this project will be documented in this file.

## [0.5.40] - 2023-09-19

### Bug Fixes

- More infor for "wrap" build
- Fix mailserver config
- Allow non-web apps, with ports without nginx proxies
- Small fix on configuration of volumes
- Fix docker-mailserver base config (wip)
- Remove web flag from nua-config
- Fix docker-mailserver conf
- Update installation method of NodeJs, deprecate NodeJs v14
- Fix linter issues
- Fix more linter issues

### Features

- Add 'post_run' to nua-config options
- Docker_start_container_name() returns a bool
- Start implementing "[run]post_run"
- Working [run]post_run, add [run]post_run_status to wait for the state of the container before exec the command, update test app docker-mailserver, version bump
- Update Ubuntu image to ubuntu:jammy-20230816

### Refactor

- Add wrapper download_url() on urlopen

### Refac

- Rename db_utils.py -> gen_db_credentials.py

## [0.5.38] - 2023-08-29

### Features

- Allow "wrap" images to use plugins as providers
- Update configuration of apps/dolibarr
- Rename providers "plugin-name" and "plugin-version" to "module-..."

## [0.5.37] - 2023-08-29

### Bug Fixes

- NO f-string for start_command, only use shell expansion
- Make invoke work even without abilian-devtools
- Increase timeout and set smaller size of chunk when saving docker image
- Temp workaround the orchestrator not finding certbot.
- Script was broken when called with no arg.
- Shorten long line.
- Forgotten "raise" and minor fixes.
- Deps.
- Boostrapper colors.
- We need newlines between log messages.
- Use tomli, not toml.
- Add dependency on snoop.
- Silence linter warning
- Proper way to deal w/ dafault positional arguments.
- Exit after sudo.
- More secure call to sudo.
- Demo-ruby doesn't build. Stashing it for now.
- More user-readable error message.
- Poetry is not needed here.
- Workaround typing issue.
- Nua build bug.
- Fix nua-cli by updating dependency on cleez.
- Verbose test level for testrunner.
- Better error messages.
- Export another function.
- Replace some print() by adhoc functions
- Nua-build tests.
- Silence mypy warning.
- Invoke 2.1.0 breaks the app
- Make README filenames consistant.
- Proper renaming of README.
- Update mail address in CODE_OF_CONDUCT.md
- Differentiate main/app as regards argv source to fix test suite
- Pattern-maching mistake.
- Apply --quiet to messages
- Tuning message verbosity
- Fix help message
- Fix argparse messages
- Allow search of packages on empty configuration
- Ensure nua venv belongs to nua
- Linter / isort a file
- Isort a skipped file
- Missing "f" in f-string.
- Linter / unused import
- Show real time status of container
- Silence linter on chmod +x
- Tweak flask/sqla demo.
- Remove changelog from nua_config
- Rename metadata "image" -> "base-image"
- Remove deprecated nua-config build/nua_dir
- Add missing release description, check unknown metadata
- Fix error import docker_sanitized_name
- Align nua-configs with the current specs.
- Comment some unused functions (at the moment)
- Try to fix strange chown bug on hedgedoc symlinks
- Install from git uses name of git package
- Make clean do rm /dist dirs
- Remove app hedgedoc branch devel
- Enforce returning an integer
- Pg_dumpall of postgres DB now working
- Fix pyright errors
- Fix lint-imports rules
- Fix option backup --all
- Use isoformat for record reference, minor fixes and refactor
- Demand that NUA_HOST is set.
- Add missing flag to a comment.
- Fix tests and typechecks, cleanup deps.
- Suppress unfinished changes to volumes
- Fix display of docker ID of image
- Fix deptry / setuptools dependency
- Fix deptry error / decorator
- Remove wrong option for deptry (ignore_obsolete)
- Remove last imports from nua.lib.db
- Import error.
- Fix broken Volume parser
- Fix deploy_utils Volume declaration
- Isort files
- Fix Volume bug in deploy_utils
- Fix test flask_mariadb_docker_wheel
- Apply isort
- Updating demo apps
- Remove duplicate postgres app test
- Fix build message
- Update examples
- Updating demo script
- Update demo.cast
- Remove deprecated test apps
- Deps:fix urllib3 error, install dictdiffer
- Fix missing function in actions.__all__
- Fix NuaConfig._data type
- Try again to fix poetry breaking on urllib3 2.0
- Fix unused import
- Fix broken options
- Fix "resource = None" situation
- Complete NuaConfigFormat and sample apps configs
- Fix NuaConfig sending None values for empty dicts
- Fix test for missing license
- Fix linter / tests
- Fix nginx template
- Fix docker utils for index error
- Fix docker utils (container listed)
- Fix render template
- Fix parsing of volume
- Fix orcherstrator.backup module path
- Fix config for test test_35_builds_sample_apps_expected_fails
- Fix db name
- Remove unused types.py
- Fix backup component description
- Simplify postgres volume name
- Do not display reports of volumes if no task
- Update volume name for mongo and marai db
- Do not display reports twice
- Fix backup date unicity
- Backup use gzip with tar
- Refactor backup plugins, remove unused
- Isort some tests
- Fix backup for multi volume container, refactor backup reports
- Fix hedgedoc nua-config
- Fix backup tar command
- Mount as nua (wip)
- Hedgedoc with sudo, backup restore postgres ok
- Fix mongo backup
- Fix lint error
- Fix backup mariadb
- Typo in postgres db plugin
- Fix volumes
- Fix sqlite plugin definition
- Fix orch for new resource parameters
- Fix plugin loading
- Fix collect of resource packages
- Replace tests for mariadb plugin
- Fix sample-apps for metadata->build sections
- Fix build.builder not always a str
- Fix demo-flask
- Fix no-license test
- Remove deprecated tests (function moved to build)
- More verbose pip install
- Fix demo-flask
- Fix letsencryp errors (wip)
- Add debug script to reset nginx conf, fixing nginx/certbot
- Add debug messages
- Fix force_list()
- Properly erase Volumes unused, update container Id after restart
- Fix missing ruby-install
- Ruby, deprecated 272, up versions to 278, 314, 322
- Fix ruby-install path
- Move deprecated ruby demo to draft-sample-apps (ruby 2.7.2 fully deprecated)
- Ruby: fix again broken ruby-install options
- Update nua-config documentation
- In nua-config format, allow value 0 for healthcheck retries
- Fix builder class detection for "wrap" images

### Documentation

- Add news/blog section.
- Add slide decks.
- Blog post on PyConFR 2023.
- Put an image above the fold.
- Add readme for the demo/screencast
- Add the new screencast and a few words.
- Fix (partly) build instructions.
- Fix (partly) build instructions.
- Update readme.
- Add apps + installation instructions.
- Fix spelling errors.
- Add some recommendations about CLI output.
- Add link to contribution doc.
- Update the CLI doc.
- Update todo
- Update / tweak readmes.
- Readmes.
- Introduce short url for installer.
- Update TODO.
- Release process.
- Describe architecture and target layering.
- Update dependency graph.
- Redraw (and show) dependency graphs.
- Regenerate graphs.
- Update dependency graphs.
- Fix typos.
- Add notes on tests and static checks in the dev doc.
- Update doc and readmes.
- Fixes and add admonitions.
- Add COC
- News/blog.
- Make warning a bit less dramatic.
- Add video from PyConFR.
- First draft about nua-config fields
- Small fixes on the nua-config doc.
- Nua-config fields completed
- Add our answers to the "Heilmeier Catechism".
- Add eye candy to readme.
- Add signature for Google search console.
- Deploy google search console signature.
- Change the [volume] list of options
- Change the [volume] list of options
- Update deps and prototype API doc.
- Use the mkdocs-material blog engine.

### Features

- Rename install script.
- Prototype for the Web UI.
- Add app admin view.
- Implement naive 'logs' commands for CLI.
- Implement or improve some nua-cli functions.
- Work a bit on the web ui.
- Improve usability of CLI.
- Add new commands to CLI.
- Add `nua server cleanup` command.
- Add `nua env` commands.
- More complete `nua env show`.
- Better argument parsing error handling.
- Add help message to 'config' command.
- Build command for nua-cli (WIP).
- Quick hack to support version.
- Call the bootstrapper with 'sudo' if needed.
- Install poetry and outdated packages.
- Add --quiet option to nua build
- Add function to test availability of local nua image
- Allow builder statement as a dict and a str
- Status show time since container creation
- Add debug util
- Prepare detection of templates need (wip)
- Improve elapsed() display
- Modify volume names (use label in first pos)
- Prepare backup script
- Add hedgedoc-devel for hedgedoc edge version package
- Upgrade base image to ubuntu:jammy-20230425
- Add restore structure code (wip)
- Backup command accepting --label or --domain or --all
- Add backup_record class
- Bump configuration of test apps
- Change color for debug message visibility
- Bump version
- More verbose on pre-build
- Add nua_config_format (wip)
- Update, bump version
- Bump version
- Use pydantic Model to validate NuaConfig
- Update, bump version
- Add --validate flag to only validate the nua-config.toml file
- Obsolete "build-command", replace build.build-command by build.build
- Add Backup class to NuaConfigFormat
- Add test validation of nuaconfig files
- Display report for backup
- Changelog, bump version
- Store backup component, all resources use the main app label_id
- Add volumes function to docker utils
- Add backup plugin for tar.gz volumes
- Add a 'backup_volume' plugin to backup all in once
- Bump version
- Uniq backup date
- Ensure backup container is pulled
- Improve backup report message
- 2 backup methods for hedgedoc
- Add resource_info to backup component
- Small refactor app_backup module
- Add backup plugin for mongodb
- Add backup plugin for mariadb
- Bump version
- Manage app.baclucp_records
- Add command: restore-backup --list to list available backups
- Bump version
- Add --last command for backup
- Implement backup restoration (wip)
- Bump version
- Fix backup, start mondodb restore
- Backup restore mariadb
- Add possible plugin new format
- Prepare new test
- Dynamic variable can call a property of a volume
- Insert detailed plugin information in resource definition at build time
- Update deps, bump version
- Allow a different syntax for resource/plugin, check on hedgedoc
- Bump version
- Resource merge from plugin with a scheme section
- Remove the scheme section
- Bump version
- Bump version
- Add test for resource without using plugin
- Add test for postgres resource without using plugin
- Add a sample app to test no plublic port apps
- Adding some test app (wip)
- Start building of sub image (wip)
- Bump version
- Add API search(), deploy_one()
- Add flag permitting nginx to fail
- Reactivate faster Certbot for known domains
- Add nua-print-deployments debug script
- Add "docker-mailserver" app (wip)

### Refactor

- Use ~nua/env instead of ~nua/nua310
- Use a dataclass.
- Replace "abort()" by "raise Abort()"
- Use Sanic instead of Starlite.
- Use webbits for html generation (experiment).
- Rename app -> cli.
- Replace Typer by home-grown CLI framework.
- Instantiate command earlier.
- Hide the empty "nua-master" package in src/
- Orchestrator cli.
- Better name.
- Split big Builder base class into 2.
- Move gen_password to nua-lib.
- Forgot to delete the old gen_password.
- Split builder module into separate modules.
- Raise specific exception on config error.
- Rename instance variables.
- Move db utils to package.
- Rename argument.
- Introduce Installer class.
- Split module.
- Split tests between unit and functional tests.
- Use argparse for CLI arg parsing.
- Don't duplicate test code for failing apps.
- Split gargantuan module into manageable ones.
- Parse config at the edge.
- Move nua-agent constants to nua-lib
- Move ArchiveSearch to nua-lib (temporarily).
- Merge nua-autobuild into nua-build.
- Fix issues introduced by the merge.
- Move NuaConfig to nua-lib (at least temporarily).
- Move docker_build_utils.py to nua-li (and rename)
- Move nua.agent.db to nua.lib.db.
- Move docker_sanitized_name() to nua.lib
- Refactor app backup (AppBackup class)
- Rename Resource eand AppInstance.volume -> .volumes
- Change Volume parameters (Volume, NuaConfig)
- Rename Resource eand AppInstance.volume -> .volumes
- Change Volume parameters (Volume, NuaConfig)
- Cleanup actions.
- Cleanup.
- Refact show_ip example.
- Remove DB code from nua-lib.
- "docker" -> "container".
- Aftermath of the nua.lib.db removal.
- Services -> LocalServices
- NuaConfig.resource -> resources
- NuaConfig.metadata.checksum -> src-checksum
- Remove NuaConfig.name (was deprecated)
- Small refactor of backcup in app_management
- Improve backup organization
- Ensure default {} or [] for possibly None values
- Refactor docker_container_of_name()
- Refactor backup format
- Refactor ports management, removing auto flag, fixing configs
- Rename restore -> restore_backup
- Small refactor of plusgins definitions
- Refactor plugin versions, add sample app to test
- Manage new plugin format
- Sepatate plugin-name/type
- Small refactor nginx configuration
- Refactor certbot to filter out internal-only deployment from certbot list
- Rename resource -> provider
- Remove some Resource specific constants
- Move metadata keys relative to sources to build section, update nua-build, real-apps configs
- Rename "meta_package" from providers to "connector"
- API, "status" command (wip)
- Refactor api.py
- Rename nginx.cmd -> nginx.commands
- Remove debug message
- Change active config storage / restore after failed deployment
- Refactoring of StateJournal
- Remove useless version.py in autobuild/

### Testing

- Fix name of dolibarr test
- Make nox and poetry play better together.
- New e2e test harness (WIP).
- Mark some tests as slow.
- E2e tests (WIP: testing build).
- We need poetry logs sometimes, after all.
- Add verbosity argument.
- Improve e2e tests reporting.
- E2e deploy tests (not working).
- E2e deploy test.
- Don't barf on first failure.
- Fix makefile for e2e tests.
- Fix e2e test + add convenience target from top makefile.
- Tweak test.
- Set apart integration tests, reactivate unit tests in CI
- Adding a new test system
- New sampple apps for postgres and sqla
- Using custom dockerfile for start.sh (see apps/sample-apps/sh_flask_show_ip)

### App_builder

- Always run build_script()

### Apps

- Add readmes for end-users.
- Tweak config / add readmes.
- Rename / move around apps in the repo.
- Update nocodb version.

### Bootstrap

- Use faster dhparam parameters when initializing nginx key

### Builder

- More explicit warning when no start script found

### Certbot

- More explicit message

### Cleanup

- Remove commented-out code.

### Debug

- Print tracebacks.

### Demo

- Make the demo script less chatty.

### Galene

- Add test in nua-config for /nua/app/galene

### Installer

- Non interactive apt install.

### Nua-build

- Add port_build_notices()

### Nua-gant

- Fix/mypy

### Nua-lib

- Fix/mypy

### Orch

- More messages normalization
- Modify some messages

### Refac

- Refactor backup plugin

### Rename

- App_builder -> app-builder.

### Tags

- Metadata.image, build.method, build.default-method

### Ui

- Use 'info' instead of 'warning'.

## [0.4.96] - 2023-02-22

### Bug Fixes

- Update setup script.
- Makefile.
- Forgot to add runtime.
- Finish refact.
- Typing issues (w/ pyright)
- Typing issues.
- Add paramiko for remote docker.
- Silence isort warning for now.
- Silence warnings + fix circular import issue.
- Workaround case (in)sensivity issue ?
- Forgot to cleanup after test
- Better messages.
- Ruff config.
- Silence rudd warning.
- Ruff warnings, deps, nox config.
- Make it proper HTML.
- Test was failing on GH.
- Fixes / cleanup.
- Hopefully this fixes the tests.
- More B028 silencing.
- Poetry warning.
- Python_package_installed + refact.
- Fix type warning.

### Continuous Integration

- Add more checks.
- Tweak noxfile.
- Github CI.
- Improve GH CI config.
- Try to fix notifications.

### Dependencies

- Add paramiko

### Documentation

- Add diagrams.
- Update README.
- Use mkdocs.
- Fix link to logo in Readme
- Deploy doc to nua.rocks.
- Update README.
- Proper img tags.
- Add matomo tracker.
- Add some stubs.
- Tweaks.
- Tweak content width.
- Configure syntax highlighting.
- Syntax highlighting.
- Tweak CLI doc.
- Format doc.
- Update README
- Add REUSE result.
- Update doc a bit.
- Fix typo.
- Update readme.
- Readme.
- Readme
- Add dependency diagrams.
- Update dependency graphs.
- Rewrite doc.
- Add link.
- Mention the invoke tasks.
- Image.md
- Publish "image" page, upgrade mkdoc-material, tweak content.
- Convert / update supporting files.
- Add top-level files to generated doc.
- Remove obsolete language from CLI doc.
- Forgot to add symlinks.
- Fix markdown.

### Features

- Add setup script for docker build image.
- Add first couple of apps.
- Start work on cli.
- WIP on demo app.
- Update apps.
- Add agent CLI and cleanup dependencies.
- Add more dependencies to setup script.
- Add commands for the remote CLI.
- Start nua-cli
- Implement a command.
- Work on nua-cli
- Server-side counterparts to nua-cli commands.
- Work on nua-cli: subcommands, cleanup...
- Improve nua-orchestrator CLI.
- Work on nua-cli.

### Refactor

- Not needed for now.
- Format.
- Cleanup test.
- Clean up tests a bit.
- Introduce "runtime" and "common" packages.
- Proposal for a DB manager API.
- Kebab casing FTW.
- Deduplicate some modules (WIP).
- Continue refactoring / cleanup.
- Define a Volume class
- Fix some warnings.
- Cleanup tests a tiny bit.
- Clearer function name.
- Use annotations from the future.
- Cleanup imports.
- This script is no longer needed.
- Better named method.
- Cleanup imports, format.
- 'global config' not needed as the config variable is never changed.
- Dependencies should go in the nua-config file.
- Group DB modules in a package.
- Rename 'error' to 'abort'.
- Cleanup a bit.
- Minor code cleanup.
- Make a package for backup
- Introduce package for certbot
- Group service-related modules together + fix mypy warnings.
- Group CLI-related modules together.
- Move boostrap to a nua-orchestrator subcommand.
- Raise exception instead of aborting.
- Small cleanup.
- Rename class Site -> AppInstance
- Rename runtime -> agent
- Remove unneeded abstraction (ensure_env).
- Split tests into unit and integration.
- Test (introduce fixture).

### Testing

- Add dummy tests.
- Forgot to add tox.ini
- Ignore 2 failing tests.
- Use hostname or env variable instead of config file.

### Tooling

- Flake8 config.
- Mypy and flake8 config.
- Add test/coverage tool.
- Coverage.
- Coverage again
- Add flake8 to pre-commit.
- Cleanup config.
- Poor man's monorepo
- Tweak monorepo tasks.
- Cleanup harder in Makefile.

### WIP

- Build scripts.
- Coding the client and agent.

### Builder

- Improve management of default_files, nua_dir

### Chose

- Start providing proper license information.

### Cleanup

- Minor code tweaks.

### Cli/orch

- Adding public key in user DB

### Debug

- Use [[assign]] for both 'site' and 'resource'
- Fix test 'flask_mariadb_docker_wheel'

### Nua

- Volumes (wip)

### Nua-build

- Rewrite using the typer module

### Nua-cli

- Conform readme and main.py

### Nua-config

- New dict syntax for dynamic ENV variables (wip)

### Nua_build

- More on config, builder class
- Fix rm_fr/rm_rf alias
- Refactoring using python docker wrapper
- Build apps/apache-basic
- Working basic apache2 package
- 2 intermediate images for smaller size
- Add full build test (tests/test_apache_basic.py)
- Bd, fix Image model
- Test for env NUA_DB_URL
- Replace package addict -> deep_access_dict
- Refactor commands for settings management, update Nua Readme
- Renaming requests.py->store.py and other small refactoring
- Allow to specify a nua_dir folder for build.py, Dockerfile...

### Nua_orchestrator

- Refactoring / flake8

### Orchestrator

- Remove mariadb intallation/configuration from bootstrap
- Reactivate nua-bootstrap

### Runtime

- Add DB managers for postgres, mariadb

### Typo

- Fix comment.

<!-- generated by git-cliff -->
