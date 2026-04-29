#!/usr/bin/env zsh
#------------------------------------------------------------------------
# A simple script that merges the latest work from "PUBLISH_BRANCH" to "main",
# pushes the updates upstream, then switches back to "PUBLISH_BRANCH" again.
# This is mostly useful if you tend to work in "PUBLISH_BRANCH", so updates are
# published immediately, and you periodically want to update "main".
#
# NOTE: finish-microsite.sh deletes this file form the repo if a separate
# publication branch is not used.
#------------------------------------------------------------------------

git checkout PUBLISH_BRANCH
git pull
git push  # make sure PUBLISH_BRANCH has been pushed upstream
git checkout main
git pull
git merge PUBLISH_BRANCH
git push
git checkout PUBLISH_BRANCH # end with PUBLISH_BRANCH checked out
