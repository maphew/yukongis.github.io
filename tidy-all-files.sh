#!/bin/bash
# Construct the full path to the config file relative to the script
config_path="${pwd}/tidy_config.txt"

# Recursively find all index.html files in subdirectories
find . -type f -name "index.html" | while read -r filepath; do
    cmd="tidy --indent yes --wrap 0 -quiet -modify \"$filepath\""
    echo "$cmd"
    eval "$cmd"
done
