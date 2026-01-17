#!/usr/bin/env bash
#
# Update main.yml across all package-update-0.14.x-* branches
# to match the version on main
#
# Uses GitHub API directly - no local checkout required!
#
# Usage:
#   ./update-package-branches-main-yml.sh [--skip-permissions] [--dry-run] [package-name]
#
# Arguments:
#   --skip-permissions    Skip approval prompts for each branch
#   --dry-run             Show what would be done without making changes
#   package-name          Optional: only update the specified package (e.g., "ams-tsl2591")
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SKIP_PERMISSIONS=false
DRY_RUN=false
SINGLE_PACKAGE=""
SOURCE_BRANCH="main"
BRANCH_PATTERN="package-update-0.14.x-"
WORKFLOW_FILE=".github/workflows/main.yml"
REPO="atopile/packages"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-permissions)
            SKIP_PERMISSIONS=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
        *)
            SINGLE_PACKAGE="$1"
            shift
            ;;
    esac
done

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Package Branch main.yml Updater${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo "Source branch: ${SOURCE_BRANCH}"
echo "Target pattern: ${BRANCH_PATTERN}*"
echo "File: ${WORKFLOW_FILE}"
echo "Dry run: ${DRY_RUN}"
echo "Skip permissions: ${SKIP_PERMISSIONS}"
echo ""

# Fetch the target main.yml content and its SHA
echo -e "${BLUE}Fetching main.yml from ${SOURCE_BRANCH}...${NC}"
SOURCE_FILE_INFO=$(gh api "repos/${REPO}/contents/${WORKFLOW_FILE}?ref=${SOURCE_BRANCH}" 2>/dev/null || echo "ERROR")

if [[ "$SOURCE_FILE_INFO" == "ERROR" || -z "$SOURCE_FILE_INFO" ]]; then
    echo -e "${RED}Error: Could not fetch main.yml from ${SOURCE_BRANCH}${NC}"
    exit 1
fi

TARGET_CONTENT=$(echo "$SOURCE_FILE_INFO" | jq -r '.content' | base64 -d)
TARGET_CONTENT_B64=$(echo "$SOURCE_FILE_INFO" | jq -r '.content' | tr -d '\n')

if [[ -z "$TARGET_CONTENT" ]]; then
    echo -e "${RED}Error: main.yml content is empty${NC}"
    exit 1
fi

echo -e "${GREEN}Successfully fetched target main.yml ($(echo "$TARGET_CONTENT" | wc -l | tr -d ' ') lines)${NC}"

# Get all matching branches
echo -e "${BLUE}Fetching branches matching pattern '${BRANCH_PATTERN}*'...${NC}"
BRANCHES=$(gh api "repos/${REPO}/branches" --paginate -q '.[].name' | grep -E "^${BRANCH_PATTERN}" | sort)

if [[ -z "$BRANCHES" ]]; then
    echo -e "${YELLOW}No branches found matching pattern${NC}"
    exit 0
fi

BRANCH_COUNT=$(echo "$BRANCHES" | wc -l | tr -d ' ')
echo -e "${GREEN}Found ${BRANCH_COUNT} branches${NC}"

# Filter to single package if specified
if [[ -n "$SINGLE_PACKAGE" ]]; then
    FILTER_BRANCH="${BRANCH_PATTERN}${SINGLE_PACKAGE}"
    if echo "$BRANCHES" | grep -q "^${FILTER_BRANCH}$"; then
        BRANCHES="$FILTER_BRANCH"
        echo -e "${BLUE}Filtering to single package: ${SINGLE_PACKAGE}${NC}"
    else
        echo -e "${RED}Error: Branch '${FILTER_BRANCH}' not found${NC}"
        echo -e "${YELLOW}Available branches:${NC}"
        echo "$BRANCHES" | head -20
        exit 1
    fi
fi

# Track results
UPDATED=()
SKIPPED=()
FAILED=()
ALREADY_UP_TO_DATE=()

echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Starting branch updates${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

for BRANCH in $BRANCHES; do
    PACKAGE_NAME="${BRANCH#${BRANCH_PATTERN}}"

    echo -e "${YELLOW}----------------------------------------${NC}"
    echo -e "${BLUE}Branch: ${BRANCH}${NC}"
    echo -e "${BLUE}Package: ${PACKAGE_NAME}${NC}"

    # Fetch current file info from the branch
    CURRENT_FILE_INFO=$(gh api "repos/${REPO}/contents/${WORKFLOW_FILE}?ref=${BRANCH}" 2>/dev/null || echo "ERROR")

    if [[ "$CURRENT_FILE_INFO" == "ERROR" || -z "$CURRENT_FILE_INFO" ]]; then
        echo -e "${YELLOW}  Warning: Could not fetch current main.yml - branch may not have the file${NC}"
        FAILED+=("$BRANCH (no main.yml)")
        continue
    fi

    CURRENT_SHA=$(echo "$CURRENT_FILE_INFO" | jq -r '.sha')
    CURRENT_CONTENT=$(echo "$CURRENT_FILE_INFO" | jq -r '.content' | base64 -d)

    # Check if already up to date
    if [[ "$CURRENT_CONTENT" == "$TARGET_CONTENT" ]]; then
        echo -e "${GREEN}  Already up to date${NC}"
        ALREADY_UP_TO_DATE+=("$BRANCH")
        continue
    fi

    # Show diff summary
    echo -e "${YELLOW}  Changes detected (showing first 15 lines):${NC}"
    DIFF_OUTPUT=$(diff <(echo "$CURRENT_CONTENT") <(echo "$TARGET_CONTENT") 2>/dev/null | head -15 || true)
    echo "$DIFF_OUTPUT" | sed 's/^/    /'

    # Request approval if not skipping
    if [[ "$SKIP_PERMISSIONS" == "false" ]]; then
        echo ""
        echo -n "  Update this branch? [y/N/q] "
        read -r REPLY

        if [[ "$REPLY" =~ ^[Qq]$ ]]; then
            echo -e "${YELLOW}Quitting...${NC}"
            break
        fi

        if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}  Skipped${NC}"
            SKIPPED+=("$BRANCH")
            continue
        fi
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}  [DRY RUN] Would update branch${NC}"
        UPDATED+=("$BRANCH (dry-run)")
        continue
    fi

    # Perform the update via GitHub API
    echo -e "${BLUE}  Updating file via GitHub API...${NC}"

    COMMIT_MESSAGE="Update main.yml from ${SOURCE_BRANCH}

Syncs GitHub Actions workflow configuration."

    # Create the update payload
    UPDATE_RESULT=$(gh api "repos/${REPO}/contents/${WORKFLOW_FILE}" \
        -X PUT \
        -f message="$COMMIT_MESSAGE" \
        -f content="$TARGET_CONTENT_B64" \
        -f sha="$CURRENT_SHA" \
        -f branch="$BRANCH" 2>&1) || true

    if echo "$UPDATE_RESULT" | jq -e '.commit.sha' > /dev/null 2>&1; then
        COMMIT_SHA=$(echo "$UPDATE_RESULT" | jq -r '.commit.sha' | head -c 7)
        echo -e "${GREEN}  Successfully updated! (commit: ${COMMIT_SHA})${NC}"
        UPDATED+=("$BRANCH")
    else
        ERROR_MSG=$(echo "$UPDATE_RESULT" | jq -r '.message // "Unknown error"' 2>/dev/null || echo "$UPDATE_RESULT")
        echo -e "${RED}  Error: ${ERROR_MSG}${NC}"
        FAILED+=("$BRANCH (API error)")
    fi
done

# Print summary
echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}======================================${NC}"

if [[ ${#UPDATED[@]} -gt 0 ]]; then
    echo -e "${GREEN}Updated (${#UPDATED[@]}):${NC}"
    for b in "${UPDATED[@]}"; do
        echo "  - $b"
    done
fi

if [[ ${#ALREADY_UP_TO_DATE[@]} -gt 0 ]]; then
    echo -e "${GREEN}Already up to date (${#ALREADY_UP_TO_DATE[@]}):${NC}"
    for b in "${ALREADY_UP_TO_DATE[@]}"; do
        echo "  - $b"
    done
fi

if [[ ${#SKIPPED[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Skipped (${#SKIPPED[@]}):${NC}"
    for b in "${SKIPPED[@]}"; do
        echo "  - $b"
    done
fi

if [[ ${#FAILED[@]} -gt 0 ]]; then
    echo -e "${RED}Failed (${#FAILED[@]}):${NC}"
    for b in "${FAILED[@]}"; do
        echo "  - $b"
    done
fi

echo ""
echo -e "${GREEN}Done!${NC}"
