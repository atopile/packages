#!/usr/bin/env bash

set -euo pipefail

find_all_packages() {
    find packages -mindepth 2 -maxdepth 2 -name "ato.yaml" -type f | \
        sed 's|/ato.yaml||' | \
        sort
}

to_json_array() {
    local input="$1"

    if [[ -z "$input" ]]; then
        echo "[]"
    else
        jq --raw-input --slurp --compact-output 'split("\n") | map(select(length > 0))' <<< "$input"
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
                packages_json=$(to_json_array "$packages")
            else
                changed_files=$(git diff --name-only "$base_ref"...HEAD -- packages/ 2>/dev/null || echo "")

                if [[ -z "$changed_files" ]]; then
                    packages_json="[]"
                else
                    changed_packages=$(
                        echo "$changed_files" | \
                        grep -E '^packages/[^/]+/' | \
                        cut -d'/' -f1,2 | \
                        sort -u
                    )
                    echo "$changed_packages"

                    packages_json=$(to_json_array "$changed_packages")
                fi
            fi
            ;;

        "workflow_dispatch"|*)
            echo "Building all packages (event: ${event_name:-unknown})" >&2
            packages=$(find_all_packages)
            packages_json=$(to_json_array "$packages")
            ;;
    esac

    echo "$packages_json"

    echo "Discovered packages: $packages_json" >&2
}

main "$@"
