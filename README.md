
# baml\_adk\_agents

[![Status: Experimental](https://img.shields.io/badge/status-experimental-yellow)](https://github.com/giladashubham/baml_adk_agents)
[![Maintained: Yes](https://img.shields.io/badge/maintained-yes-brightgreen)](https://github.com/giladashubham/baml_adk_agents)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/giladashubham/baml_adk_agents?style=social)](https://github.com/giladashubham/baml_adk_agents/stargazers)

Minimal Python project integrating ADK with BAML using [uv](https://astral.sh/uv/).

## ⚙️ Quickstart

```bash
git clone https://github.com/giladashubham/baml_adk_agents.git
cd baml_adk_agents
uv sync
cp .env_copy .env  # Add your LLM API keys
uv run baml_runner.py
```

## 📁 Structure

* `baml_adk_agent.py` – Agent logic
* `baml_runner.py` – Entry point
* `baml_src/` – BAML source files
* `.env_copy` – Example environment configuration

## 🛠️ Requirements

* Python (managed via `uv`)
* LLM API keys (e.g., OpenAI)


Certainly! Here's a comprehensive `README.md` file tailored for the [giladashubham/baml\_adk\_agents](https://github.com/giladashubham/baml_adk_agents/tree/main) repository. This project utilizes the `uv` Python package manager for efficient environment and dependency management.


## License

This project is licensed under the [MIT License](LICENSE).

