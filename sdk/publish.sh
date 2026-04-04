#!/bin/bash
# Publish Semantys AI SDKs to PyPI and npm
# Usage: ./publish.sh [python|typescript|all]

set -e

TARGET=${1:-all}

publish_python() {
    echo "=== Publishing Python SDK to PyPI ==="
    cd "$(dirname "$0")/python"
    pip install build twine --quiet
    rm -rf dist/ build/ *.egg-info
    python -m build
    echo ""
    echo "Built packages:"
    ls -la dist/
    echo ""
    echo "To upload to PyPI:  twine upload dist/*"
    echo "To upload to TestPyPI:  twine upload --repository testpypi dist/*"
    cd -
}

publish_typescript() {
    echo "=== Publishing TypeScript SDK to npm ==="
    cd "$(dirname "$0")/typescript"
    npm install
    npm run build
    echo ""
    echo "Built package. To publish:"
    echo "  npm publish              # public publish"
    echo "  npm publish --dry-run    # dry run first"
    cd -
}

case $TARGET in
    python)
        publish_python
        ;;
    typescript)
        publish_typescript
        ;;
    all)
        publish_python
        echo ""
        publish_typescript
        ;;
    *)
        echo "Usage: $0 [python|typescript|all]"
        exit 1
        ;;
esac

echo ""
echo "Done! Remember to:"
echo "  1. Update version numbers before publishing"
echo "  2. Test with --dry-run or TestPyPI first"
echo "  3. Tag the release: git tag v0.1.0 && git push --tags"
