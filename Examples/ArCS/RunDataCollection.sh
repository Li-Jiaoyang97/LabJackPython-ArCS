#!/usr/bin/env bash
set -u
#values=(-5.0 -6.0)
values=(-5.0 -6.0 -7.0 -8.0 -9.0 -10.0)

for v in "${values[@]}"; do
     echo "Running: python3 ArCSHVMonitor.py 3 $v 5 $1"
     python3 ArCSHVMonitor.py 3 "$v" 5 "$1"
done
