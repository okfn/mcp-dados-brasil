# MCP dados Brasil

This repository contains declarative dataset definitions for the
[Brasil open data portal](https://dados.gov.br).  

**Note:** This is a work in progress at Alpha stage.  

This ready to run with the OKFN MCP server defined at https://github.com/okfn/mcp-ckan.  

## Add this to a OKFN MCP server

Add this repository to your MCP server configuration at the `deploy/tool_sources.yaml` file:

```yaml
  - name: mcp-dados-brasil
    repo: git@github.com:okfn/mcp-dados-brasil.git
    # path is the place in which the MCP tools live
    path: datasets
    ref: main
    # if the repo is private, use a key
    # This private key file should be generated with something like
    # ssh-keygen -t ed25519 -f keys/mcp-dados-brasil-key -N "" -C "deploy@mcp-server"s
    # and then add this public key to the GitHub repo's deploy keys (with read access, it'll be enough)
    # This key must be deployed in the MCP server's filesystem at the path specified below, and the private key file must have permissions set to 600 (read/write for owner only)
    key: deploy/keys/mcp-dados-brasil-key
```

## How it works

Each `.yaml` file defines a dataset and its MCP tools declaratively. No Python code is needed.

## Adding a new dataset

1. Create a new `.yaml` file in `datasets/`
2. Set the proper `engine`. Read about them at https://github.com/okfn/mcp-ckan/tree/main/src/mcp_server/engines
3. Define the `dataset` metadata and `source` (CSV URL)
4. Define `tools` with their parameters and logic
5. Push to this repo and re-fetch on the MCP server
