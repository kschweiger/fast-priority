#!/bin/sh

OLD_VERSION=$(uv run --frozen python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

echo "Bumping Version"

uv run --frozen python bump.py . $1
if [[ $? != 0 ]]; then
  echo "Bumping version failed. Exiting..."
  exit 1
fi

if ! uv lock --no-config --default-index https://pypi.org/simple; then
  echo "Updating uv.lock failed. Exiting..."
  exit 1
fi

VERSION=$(uv run --frozen python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

echo $VERSION

git-changelog --bump ${VERSION}

git add pyproject.toml CHANGELOG.md uv.lock
git commit -n -m "build: Bumping ${OLD_VERSION} -> ${VERSION} 🔖"

git tag ${VERSION}

echo "Pushing"
git push

echo "Pushing tag"
git push --tag
