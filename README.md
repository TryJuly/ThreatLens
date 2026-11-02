# ThreatLens

python3 --version
python3 -m venv .venv
source .venv/bin/activate
pip install asyncssh

ssh -p 2222 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@127.0.0.1