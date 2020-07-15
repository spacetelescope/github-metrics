#!/usr/bin/env bash

set -e
cd /Users/jcurtin/workspace/github-metrics/service
if [ ! -d "logs" ]; then
    mkdir logs
fi
source env/bin/activate
PATH="/home/jcurtin/workspace/bert-etl/bin:$PATH" \
    PYTHONPATH="/home/jcurtin/workspace/bert-etl" \
    AWS_PROFILE=stsci bert-runner.py -m collectMetrics -f 2>>logs/stderr.log >>logs/stdout.log
deactivate
cd -
