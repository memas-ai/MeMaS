# MeMaS: a Long Term Memory Store for AI Chatbots and Agents
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![](https://dcbadge.vercel.app/api/server/j2NvzK5qN7?compact=true&style=flat)](https://discord.gg/j2NvzK5qN7)

**MeMaS**, abbreviated from Memory Management Service, is a Long Term Memory Store designed for AI Chatbots and Agents. We offer a simple memory abstraction (`recall` and `memorize`), as well as tools for admins to manage memory.

## Why MeMaS?
- A dedicated solution for chatbot/agent memory. 
    - Works out of the box and APIs easy to integrate.
    - We save you the time and effort to implement your own memory.
- Store knowledge as well as chat memory. 
    - Use for Retrieval Augmented Generation and can reduce hallucination.
    - Reduce need of fine tuning/retraining.
- Manage what the chatbot knows through Corpuses and Access Control
    - Improved visibility and debuggability, parts of LLMs are no longer black boxes
    - Fine grain and real time control over even individual chatbots

## Get Started
### Examples
Examples are posted in https://github.com/memas-ai/memas-examples.

### Setting up the server
TODO, right now follow [CONTRIBUTING.md](CONTRIBUTING.md)
### Client and SDK
We offer client and sdks in 5 languages. Read more in the [api package](https://github.com/memas-ai/MeMaS-api). Example for python:
```
pip install memas-client
pip install memas-sdk
```
Notice that there's both a `memas-client` and a `memas-sdk`. Read more in our documentation! TODO: add hyperlink 

## Contributing
As an opensource project, contributors are extremely welcome! Read [CONTRIBUTING.md](CONTRIBUTING.md) for more details. 

Also join our community discord server, linked at the top!
