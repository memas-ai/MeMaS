# MeMaS

### Development Setup
Run `source setup-env.sh`, this will install all the needed development tools.

TODO: More to come with how to run things with docker

### Running Docker
In the top level of this repo, run `docker compose up`, and it will spin up 3 es nodes, 3 scylla nodes, 1 milvus node, and a few more. This setup is meant to test 

May need to run `sysctl -w vm.max_map_count=262144`.
