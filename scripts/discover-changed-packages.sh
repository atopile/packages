#!/usr/bin/env bash

set -euo pipefail

find_all_packages() {
    find packages -mindepth 2 -maxdepth 2 -name "ato.yaml" -type f | \
        sed 's|/ato.yaml||' | \
        sort
}

to_json_array() {
    if [[ -z "$1" ]]; then
        echo "[]"
    else
        jq --raw-input --slurp --compact-output 'split("\n") | map(select(length > 0))' <<< "$1"
    fi
}

main() {
    local event_name="${1:-}"
    local base_ref="${2:-}"
    local packages_json=""

    case "$event_name" in
        "pull_request"|"push")
            if [[ -z "$base_ref" ]]; then
                echo "Error: base_ref is required for $event_name events" >&2
                exit 1
            fi

            if [[ "$base_ref" =~ ^0+$ ]]; then  # base_ref is the first commit
                echo "Initial commit detected, building all packages" >&2
                packages=$(find_all_packages)
                packages_json=$(echo -n "$packages" | to_json_array)
            else
                changed_files=$(git diff --name-only "$base_ref"...HEAD -- packages/ 2>/dev/null || echo "")

                changed_packages=$(
                    echo "$changed_files" | \
                    grep -E '^packages/[^/]+/' | \
                    cut -d'/' -f1,2 | \
                    sort -u
                )

                packages_json=$(echo -n "$changed_packages" | to_json_array)
            fi
            ;;

        "workflow_dispatch"|*)
            echo "Building all packages (event: ${event_name:-unknown})" >&2
            packages=$(find_all_packages)
            packages_json=$(echo -n "$packages" | to_json_array)
            ;;
    esac

    echo "$packages_json"

    echo "Discovered packages: $packages_json" >&2
}

main "$@"
