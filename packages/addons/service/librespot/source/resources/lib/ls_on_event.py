#!/usr/bin/python3

import os
import json

PIPE_PATH = "/tmp/librespot"

# Throw all environment variables except for system ones
variables = dict()
for k, v in dict(os.environ).items():
    if not (k.endswith("PATH") or k.startswith("PULSE") or k.startswith("RUST")):
        variables[k] = v

variables = json.dumps(variables, separators=(',', ':'))

# Open named unix socket
path = "/tmp/librespot"
try:
    os.mkfifo(path)
except OSError:
    pass

with open(PIPE_PATH, 'a') as fifo:
    fifo.write(variables)
    fifo.write('\n')
    fifo.close()
