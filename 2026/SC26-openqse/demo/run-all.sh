#!/bin/bash
# Run every section of the tutorial in order. DEMO_AUTO=1 skips the pauses.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
for part in 00-start 01-resource-graph 02-owned-device 03-vendor-queue 04-what-the-job-sees 05-side-quests; do
    bash "$here/$part.sh"
done
