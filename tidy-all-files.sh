#!/bin/bash
# Construct the full path to the config file relative to the script
config_path="${pwd}/tidy_config.txt"

# Recursively find all index.html files in subdirectories
find . -type f -name "index.html" | while read -r filepath; do
    echo "Processing $filepath with config at $config_path"
    tidy -config "$config_path" -m "$filepath"

    if [ $? -ne 0 ]; then
        echo "tidy failed on $filepath"
    fi
done
