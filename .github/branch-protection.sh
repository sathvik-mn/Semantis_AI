#!/bin/bash
# Apply branch protection rules to the main branch
# Prerequisites: gh CLI installed and authenticated (gh auth login)
# Usage: bash .github/branch-protection.sh

set -e

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Applying branch protection to $REPO (main branch)..."

gh api repos/$REPO/branches/main/protection \
  --method PUT \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["Backend Lint & Check", "Backend Tests", "Frontend Lint & Type Check"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF

echo "Branch protection applied successfully!"
echo ""
echo "Rules set:"
echo "  - Require PR with 1 approval before merging"
echo "  - Dismiss stale reviews on new pushes"
echo "  - Require CI checks to pass (lint + tests)"
echo "  - No force pushes or branch deletion"
