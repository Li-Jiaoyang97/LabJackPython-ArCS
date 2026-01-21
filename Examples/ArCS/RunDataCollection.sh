#!/usr/bin/env bash
set -u
#values=(-5.0 -6.0)
#values=(-5.0 -7.0 -9.0 -10.0 -13.0 -15.0 -20.0 -23.0 -24.0 -25.0 -26.0 -27.0 -30.0 -40.0 -50.0 -70.0)
values=(-0.0)

for v in "${values[@]}"; do
     echo "Running: python3 ArCSHVMonitor.py 3 $v 5 $1"
     python ArCSHVMonitor.py 3 "$v" 5 "$1"
done
