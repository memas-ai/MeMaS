# Contributing to MeMaS
Hi there! Thank you for even being interested in contributing to MeMaS. As an open source project in a rapidly developing field, we are extremely open to contributions, whether they be in the form of new features, improved infra, better documentation, or bug fixes.

To contribute to this project, please follow the [fork and pull request](https://docs.github.com/en/get-started/quickstart/contributing-to-projects) workflow. Please do not try to push directly to this repo unless you are maintainer. 

**For new features/bigger changes, talk to maintainers in the discord before you set off.**

## Development Guide

### Prerequiste
Python 3.10, [Docker](https://www.docker.com/), and Linux (or WSL). The code breaks on python 3.8 and below, and 3.9 is untested.

If you are working using WSL, follow this guide to [configure Docker](https://docs.docker.com/desktop/wsl/). And for first time WSL users, I HIGHLY recommend cloning MeMaS directly into your WSL file system.
### Development Setup

Run `source setup-env.sh`, this will install all the needed development tools, as well as setup the needed environment variables. 

**And please run `source format.sh` before each commit!**

**NOTE that this command needs to be ran for each new shell instance, since it sets up environment variables.**
### Using Docker
In the top level of this repo, run 

```bash
docker compose --profile dev up --build
```

This will spin up 1 MeMaS instance running in gunicorn, 1 es nodes, 1 scylla nodes, 1 milvus node, and a few more. This is a very basic development setup.

To stop docker execution, run Control+C in the terminal you are running `docker compose up`, or run `docker compose down`.

If you want to clean your local docker images, run 
```bash
docker compose down --volumes
```

FYI you may need to run `sysctl -w vm.max_map_count=262144` if you get an error when trying to start elasticsearch.

### Developing with local MeMaS outside of Docker
If you only need the MeMaS dependencies and want to run flask/gunicorn locally outside of docker, run this instead to bring up the dependencies in docker:

```bash
docker compose up
```

If this is your first time initializing the MeMaS server, after `docker compose up` and wait till the dependencies are fully started, run `source setup-env.sh`, then

```bash
flask --app 'memas.app:create_app(config_filename="memas-config.yml", first_init=True)' run
```

This will run for a while then exit. Upon exit, your MeMaS is properly setup. **NOTE: Only run this phase when you are working with a clean set of docker dependencies, aka a fresh start or after `docker compose down --volumes`.**

After MeMaS is properly initialized, run `source setup-env.sh`, then:
```bash
flask --app 'memas.app:create_app(config_filename="memas-config.yml")' run
``` 
to start the memas server.

And to run the app with wsgi server, run
```bash
gunicorn -w 1 -k eventlet 'memas.app:create_app(config_filename="memas-config.yml")'
```
note `-w` sets the number of worker threads. 

### Running Integration Tests
After `source setup-env.sh` and `docker compose up`, wait till the services are fully started.

Then run 
```bash
python3 -m pytest integration-tests
```

**NOTE: MeMaS server is not needed for this**