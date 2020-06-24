#!/usr/bin/env bash

set -e
cd /Users/jcurtin/workspace/github-metrics/service
mkdir logs
source env/bin/activate
AWS_PROFILE=stsci bert-runner.py -m collectMetrics -f 2>>logs/stderr.log >>logs/stdout.log
deactivate
cd -
