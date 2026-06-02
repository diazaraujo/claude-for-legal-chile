#!/bin/bash
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
python3 scripts/refresh/refresh.py --cadence weekly
bash scripts/refresh/refresh-rsync-enigma.sh
bash scripts/refresh/refresh-downstream.sh
