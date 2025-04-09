#!/bin/bash

# Store the original directory
ORIGINAL_DIR=$(pwd)

# Arrays to store results
declare -a successful_builds=()
declare -a failed_builds=()

# Function to handle errors
handle_error() {
    echo "❌ Error occurred in directory: $1"
    failed_builds+=("$1")
    cd "$ORIGINAL_DIR/packages"
    return 1
}

# Change to packages directory
cd packages

# Loop through all directories
for dir in */; do
    if [ -d "$dir" ]; then
        echo "🔨 Building package in $dir with arguments: $@"
        if (cd "$dir" && ato build "$@"); then
            echo "✅ Successfully built $dir"
            successful_builds+=("$dir")
        else
            handle_error "$dir"
            # Continue to next directory even if this one failed
            continue
        fi
    fi
done

# Return to original directory
cd "$ORIGINAL_DIR"

# Print summary report
echo -e "\n📊 Build Summary Report"
echo "====================="
echo -e "\n✅ Successful builds (${#successful_builds[@]}):"
for build in "${successful_builds[@]}"; do
    echo "  - $build"
done

echo -e "\n❌ Failed builds (${#failed_builds[@]}):"
for build in "${failed_builds[@]}"; do
    echo "  - $build"
done

echo -e "\n📈 Total packages: $((${#successful_builds[@]} + ${#failed_builds[@]}))"
echo "✅ Successful: ${#successful_builds[@]}"
echo "❌ Failed: ${#failed_builds[@]}"

# Exit with error if any builds failed
if [ ${#failed_builds[@]} -gt 0 ]; then
    exit 1
fi
