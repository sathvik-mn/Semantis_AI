# Publishing Guide for Semantys Cache SDK

## ✅ Package Build Status

The package has been built successfully! Distribution files are in `dist/` directory.

## 📦 Python Package (PyPI)

### Pre-built Files
- `dist/semantys-cache-1.0.0.tar.gz` (source distribution)
- `dist/semantys_cache-1.0.0-py3-none-any.whl` (wheel)

### Test Installation (Local)

```bash
# Install from local build
pip install dist/semantys_cache-1.0.0-py3-none-any.whl

# Or install in development mode
pip install -e .
```

### Publish to PyPI

#### Prerequisites
1. Create PyPI account: https://pypi.org/account/register/
2. Create API token: https://pypi.org/manage/account/token/
3. Install twine: `pip install twine`

#### Test PyPI (Recommended First)

```bash
cd sdk/python-wrapper

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ semantys-cache
```

#### Production PyPI

```bash
cd sdk/python-wrapper

# Upload to PyPI (requires API token)
twine upload dist/*

# Install from PyPI
pip install semantys-cache
```

#### Environment Variables for Publishing

```bash
# Option 1: Use environment variables
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-<your-api-token>

# Option 2: Use .pypirc file (create in home directory)
# [pypi]
# username = __token__
# password = pypi-<your-api-token>
```

### Verify Publication

```bash
# Check package on PyPI
# Visit: https://pypi.org/project/semantys-cache/

# Install and test
pip install semantys-cache
python -c "from semantys_cache import SemanticCache; print('OK')"
```

## 📦 TypeScript Package (npm)

### Prerequisites
1. Create npm account: https://www.npmjs.com/signup
2. Login: `npm login`
3. Install dependencies: `npm install`

### Build Package

```bash
cd sdk/typescript

# Install dependencies
npm install

# Build (if TypeScript compilation is needed)
npm run build
```

### Publish to npm

```bash
cd sdk/typescript

# Test locally first
npm pack
npm install semantys-cache-1.0.0.tgz

# Publish to npm
npm publish

# Or publish with tag
npm publish --tag beta
```

### Verify Publication

```bash
# Check package on npm
# Visit: https://www.npmjs.com/package/semantys-cache

# Install and test
npm install semantys-cache
node -e "const { SemanticCache } = require('semantys-cache'); console.log('OK')"
```

## 🔄 Update Version

### Python Package

1. Update version in:
   - `setup.py`: `version="1.0.1"`
   - `pyproject.toml`: `version = "1.0.1"`
   - `semantys_cache/__init__.py`: `__version__ = "1.0.1"`

2. Rebuild and publish:
   ```bash
   cd sdk/python-wrapper
   python -m build
   twine upload dist/*
   ```

### TypeScript Package

1. Update version in `package.json`: `"version": "1.0.1"`

2. Publish:
   ```bash
   cd sdk/typescript
   npm publish
   ```

## 📝 Notes

1. **First Time Publishing**: Test on Test PyPI first to avoid mistakes
2. **Version Numbers**: Follow semantic versioning (MAJOR.MINOR.PATCH)
3. **Credentials**: Never commit API tokens or passwords to git
4. **Documentation**: Ensure README.md is up to date before publishing
5. **Testing**: Test installation from PyPI/npm before announcing

## ✅ Checklist Before Publishing

- [ ] Version number updated
- [ ] README.md is accurate
- [ ] All dependencies listed in setup.py/package.json
- [ ] License file included (MIT)
- [ ] Package builds successfully
- [ ] Local installation works
- [ ] Import works: `from semantys_cache import SemanticCache`
- [ ] Basic functionality tested
- [ ] API tokens/credentials ready
- [ ] Test PyPI/npm tested first (recommended)

## 🚀 Quick Start (After Publishing)

### Python

```bash
pip install semantys-cache
python -c "from semantys_cache import SemanticCache; print('Installed successfully!')"
```

### TypeScript

```bash
npm install semantys-cache
node -e "const { SemanticCache } = require('semantys-cache'); console.log('Installed successfully!')"
```

## 📞 Support

If you encounter issues:
1. Check PyPI/npm package page for errors
2. Verify credentials are correct
3. Ensure package name is available (not taken)
4. Check version number is unique
5. Review build logs for errors

---

**Status**: ✅ Package built and ready for publishing
**Next Step**: Get PyPI/npm credentials and publish!

