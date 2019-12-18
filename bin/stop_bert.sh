#!/bin/bash
set -x
ps ux | awk '$12 ~ /bert-serving-start/ {print $2}' | xargs -I {} kill -9 {}
echo "bert kill ok"
ps ux | awk '$12 ~ /bert-serving-start/ {print $2}' | xargs -I {} echo {}