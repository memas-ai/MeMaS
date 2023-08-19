# MeMaS

## Development Setup
Run `source setup-env.sh`, this will install all the needed development tools, as well as setup the needed environment variables.

### Running Docker
In the top level of this repo, run `docker compose up`, and it will spin up 1 es nodes, 1 scylla nodes, 1 milvus node, and a few more. This is a very basic development setup.

May need to run `sysctl -w vm.max_map_count=262144`.

### Initializing the MeMaS server
Due to the dependencies, the first time running MeMaS, we need to use a special command to initialize and configure the dependencies.

After `source setup-env.sh` and `docker compose up`, wait till the services are fully started.

Then run 
```
flask --app 'memas.app:create_app(config_filename="memas-config.yml", first_init=True)' run
```

This will run for a while then exit. Upon exit, your MeMaS is properly setup.

### Running the MeMaS server
After `source setup-env.sh` and `docker compose up`, wait till the services are fully started.

Then run 
```
flask --app 'memas.app:create_app(config_filename="memas-config.yml")' run
``` 
to start the memas server

To run the app with wsgi server, run
```
gunicorn -b :8010 -w 1 -k eventlet 'memas.app:create_app(config_filename="memas-config.yml")'
```
note `-w` sets the number of worker threads. 

### Running Integration Tests
After `source setup-env.sh` and `docker compose up`, wait till the services are fully started.

Then run 
```
python3 -m pytest integration-tests
```

## Benchmarking
For running benchmarking, you need to first create an OpenAI API Key. This is a good [tutorial](https://www.geeksforgeeks.org/how-to-use-chatgpt-api-in-python/).

Then after having a running instance of memas, run

```
export OPENAI_API_KEY=your_api_key; python3 -m benchmarking
```
