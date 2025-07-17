# Audit log API - Code Challenges

## How to set up Backend Server

```bash
# (optional) instal virtual envs, we require version of python
conda create --name yourenv python==3.10.0
conda actiate yourenv

# install env package
git clone https://github.com/thinhsuy/audit-log-api.git
cd audit-log-api

# install and start API
pip install poetry
poetry config virtualenvs.create false
cd api && poetry install
cd api/core && python main.py
```