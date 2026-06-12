#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    FastAPI Route - Clean Test Files  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo -e "${YELLOW}Cleaning test output directories...${NC}"
echo ""

# Remove test output directories and files
echo -e "${BLUE}Removing:${NC}"

# Coverage HTML report
echo -e "  - tests/coverage_html/"
if [ -d "tests/coverage_html" ]; then
    rm -rf tests/coverage_html
    echo -e "    ${GREEN}✓ Removed${NC}"
else
    echo -e "    ${YELLOW}⚠ Not found${NC}"
fi

# Coverage XML report
echo -e "  - tests/coverage.xml"
if [ -f "tests/coverage.xml" ]; then
    rm -f tests/coverage.xml
    echo -e "    ${GREEN}✓ Removed${NC}"
else
    echo -e "    ${YELLOW}⚠ Not found${NC}"
fi

# .pytest_cache
echo -e "  - .pytest_cache/"
if [ -d ".pytest_cache" ]; then
    rm -rf .pytest_cache
    echo -e "    ${GREEN}✓ Removed${NC}"
else
    echo -e "    ${YELLOW}⚠ Not found${NC}"
fi

# .coverage files
echo -e "  - .coverage"
if [ -f ".coverage" ]; then
    rm -f .coverage
    echo -e "    ${GREEN}✓ Removed${NC}"
else
    echo -e "    ${YELLOW}⚠ Not found${NC}"
fi

echo -e "  - .coverage.*"
if ls .coverage.* 1>/dev/null 2>&1; then
    rm -f .coverage.*
    echo -e "    ${GREEN}✓ Removed${NC}"
else
    echo -e "    ${YELLOW}⚠ Not found${NC}"
fi

# HTML coverage from root
echo -e "  - htmlcov/"
if [ -d "htmlcov" ]; then
    rm -rf htmlcov
    echo -e "    ${GREEN}✓ Removed${NC}"
else
    echo -e "    ${YELLOW}⚠ Not found${NC}"
fi

# Python cache files
echo -e "  - **/__pycache__/"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo -e "    ${GREEN}✓ Removed${NC}"

# .pyc files
echo -e "  - **/*.pyc"
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "    ${GREEN}✓ Removed${NC}"

echo ""
echo -e "${GREEN}✓ Clean completed!${NC}"
echo ""
echo -e "${YELLOW}To re-run tests with coverage, use: ./scripts/test.sh${NC}"
echo -e "${BLUE}========================================${NC}"