#!/usr/bin/env zsh
#------------------------------------------------------------------------
# Convert this microsite template into your desired microsite.
# Run finish-microsite.sh -h to see the required arguments and options.
# Note: This file defaults to use zsh. If you don't have zsh, but you
# DO have bash v5+, then use /path/to/bash finish-microsite.sh.
#------------------------------------------------------------------------

ymdformat="%Y-%m-%d"
tsformat="$ymdformat %H:%M %z"
script=$0
dir=$(dirname $script)
cfg="$dir/docs/_config.yml"
index="$dir/docs/index.markdown"
work_branch=main
publish_branch=main
default_assignees="deanwampler,adampingel,jolson-ibm"

dashboard_base="The-AI-Alliance"
default_dashboard_number=39
default_dashboard_name="Misc. Alliance Tasks"

help() {
	cat << EOF
$script [options] \
  -t|--site-title|--microsite-title title

These arguments are required, but they can appear in any order, intermixed
with optional arguments (discussed below). See the example below:

-t | --site-title | --microsite-title title
                       The title of the microsite.

These arguments are optional:
-h | --help            Print this message and exit.
-n | --noop            Just print the commands but don't run them.

-s | --next-steps      At the end of running this script to create a new repo,
                       some information about "next steps" is printed. If you want to see
                       this information again, run this script again just using this flag.
-r | --repo-name name  The name of GitHub repo. If you are running this script in the
                       repo's root directory, its name will be used, by default.
-d | --dashboard N     The "N" for the ${dashboard_base}/N link to use for the project's dashboard.
                       Default: "$default_dashboard_number" ("$default_dashboard_name").
-a | --assignees list  Comma-separated list of GitHub user names to whom issues are assigned.
                       E.g., "--assignees bob,ted". Default: "$default_assignees".
--use-latest           By default, this script previously assumed that you would publish
                       the website from the "latest" branch, while using "main" for integration.
                       This is difficult for less-technical users. Now the default is to use 
                       "main", but if you prefer to use "latest" as the publish branch, use
                       this option. See also "--publish-branch BR".
--publish-branch BR    Instead of publishing from "main" (or "latest"; see "--use-latest"),
                       set up "BR" as the branch used for publishing the website.
--no-push              Normally, all edits are pushed upstream to the GitHub repo. Use this option
                       skip that step, for example if your plan to make additional edits first or
                       when debugging this script!! ;)

For example, suppose you want to create a microsite with the title "AI for Evil Project", 
then use this command:

$script --microsite-title "AI for Evil Project"

EOF
}

repo_name=

next_steps() {
	local repo_name="$1"
	cat << EOF

Next Steps:

Return to README-instructions.md for any additional instructions to follow:

  Local copy: README-instructions.md
  GitHub:     https://github.com/The-AI-Alliance/$repo_name/blob/main/README-instructions.md

Don't forgot to commit and push any subsequent changes upstream, e.g., "git push --all".
You also need to do this if you used the "--no-push" option.

To see these instructions again, run the following command:

  $script --next-steps
EOF
}

error() {
	for arg in "$@"
	do
		echo "ERROR ($script): $arg"
	done
	echo "ERROR: Try: $script --help"
	exit 1
}

warn() {
	for arg in "$@"
	do
		echo "WARN  ($script): $arg"
	done
}

info() {
	for arg in "$@"
	do
		echo "INFO  ($script): $arg"
	done
}

determine_dashboard() {
	n=$1
	if [[ $n -ge 1 ]]
	then
		# User input valid number
		dashboard="${dashboard_base}/$n"
	else
		# User input a full URL (hopefully!)
		dashboard="$n"
	fi
	echo $dashboard
}

determine_dashboard_url() {
	n=$1
	if [[ $n -ge 1 ]]
	then
		# User input valid number
		dashboard_url="https://github.com/orgs/${dashboard_base}/projects/$n/"
	else
		# User input a full URL (hopefully!)
		dashboard_url="$n"
	fi
	echo $dashboard_url
}

dashboard=$(determine_dashboard $default_dashboard_number)
dashboard_url=$(determine_dashboard_url $default_dashboard_number)
assignees="$default_assignees"
do_push=true
show_next_steps=false
while [[ $# -gt 0 ]]
do
	case $1 in
		-h|--h*)
			help
			exit 0
			;;
		-n|--noop)
			NOOP=echo
			;;
		-s|--next-steps)
			show_next_steps=true
			;;
		-r|--repo-name)
			shift
			repo_name="$1"
			;;
		-t|--site-title|--microsite-title)
			shift
			microsite_title="$1"
			;;
		-d|--site-description|--microsite-description)
			shift
			microsite_description="$1"
			;;
		--dashboard)
			shift
			dashboard=$(determine_dashboard "$1")
			dashboard_url=$(determine_dashboard_url "$1")
			;;
		-a|--assignees)
			shift
			assignees="$1"
			;;
		--use-latest)
			publish_branch="latest"
			;;
		--publish-branch)
			shift
			publish_branch="$1"
			;;
		--no-push)
			do_push=false
			;;
		*)
			error "Unrecognized argument: $1"
			;;
	esac
	shift
done

[[ -z "$repo_name" ]] && repo_name=$(basename $PWD)

$show_next_steps && next_steps $repo_name && exit 0


get_value() {
	current=$1
	prompt=$2
	non_empty_required=$3

	value=$current
	reqd=
	[[ -n $non_empty_required ]] && reqd=" (required)"

	while true
	do
		vared -p "$prompt$reqd> " value
		if [[ -n $value ]] || [[ -z $non_empty_required ]]
		then
			echo $value
			return 0
		fi
	done
}

if [[ -z "$microsite_title" ]] || [[ -z "$repo_name" ]]
then
	# Prompt the user for values:
	echo "Prompting for the information I need."
	echo "If a current value shown after the '>' is correct, just hit return to use it."
	
	microsite_title=$(get_value "$microsite_title" "Microsite title" true)
	microsite_description=$(get_value "$microsite_description" "Short microsite description" true)	
	repo_name=$(get_value "$repo_name" "Repository name" true)	
	work_branch=$(get_value "$work_branch" "Work (integration) branch name" true)
	publish_branch=$(get_value "$publish_branch" "Website publication branch name" true)
	db=$(get_value "$dashboard" "Project dashboard (number)")
	dashboard=$(determine_dashboard "$db")
	dashboard_url=$(determine_dashboard_url "$db")
	assignees=$(get_value "$assignees" "Issue and PR assignees")	
	do_push=$(get_value "$do_push" "Push changes to GitHub? Enter true or false")
fi

missing=()
[[ -z "$microsite_title" ]] && missing+=("The microsite title is required. ")
[[ ${#missing[@]} > 0 ]] && error "${missing[@]}"

info "New values for the repo:"
info "  Repo name:                $repo_name"
info "  Title:                    $microsite_title"
info "  Description:              $microsite_description"
info "  GitHub:"
[[ -n "$dashboard" ]] && \
  info "    Dashboard:              $dashboard"
  info "    Dashboard URL:          $dashboard_url"
[[ -n "$assignees" ]] && \
  info "    Issue assignees:        $assignees"
info "    Work branch:            $work_branch"
info "    Publishing branch:      $publish_branch"
info "    Push changes to GitHub? $do_push"

info "Replacing the microsite-template README.md with the new README-template.md:"
$NOOP git rm README.md
$NOOP git mv README-template.md README.md

info "Replacing macro placeholders with the new values:"
[[ -z "$ymdtimestamp" ]] && ymdtimestamp=$(date +"$ymdformat")
date -j -f "$ymdformat" +"$ymdformat" "$ymdtimestamp" > /dev/null 2>&1
[[ $? -ne 0 ]] && error "Invalid YMD timestamp format for timestamp: $ymdtimestamp" "Required format: $ymdformat"
[[ -z "$timestamp" ]] && timestamp=$(date +"$tsformat")
date -j -f "$tsformat" +"$tsformat" "$timestamp" > /dev/null 2>&1
[[ $? -ne 0 ]] && error "Invalid timestamp format for timestamp: $timestamp" "Required format: $tsformat"

other_files=(
	Makefile
	update-main.sh
	docs/_config.yml
)
markdown_files=($(find docs -name '*.markdown') $(find . -name '*.md'))
html_files=($(find docs/_layouts docs/_includes -name '*.html'))
github_files=($(find .github \( -name '*.yaml' -o -name '*.md' \)))

info "Replacing macros with correct values:"
info "  REPO_NAME:              $repo_name"
info "  MICROSITE_TITLE:        $microsite_title"
info "  MICROSITE_DESCRIPTION:  $microsite_description"
info "  DASHBOARD_URL:          $dashboard_url"
info "  DASHBOARD:              $dashboard"
info "  PUBLISH_BRANCH:         $publish_branch"
info "  ASSIGNEES:              $assignees"
info "  YMD_TSTAMP:             $ymdtimestamp"
info "  TIMESTAMP:              $timestamp"
info


if [[ $work_branch = $publish_branch ]]
then
	info "You are publishing the website from the work branch: $work_branch."
	info "Deleting the update-main.sh script, which you don't need."
	info
	$NOOP git rm update-main.sh
fi

info "Processing Files:"

for file in "${other_files[@]}" "${markdown_files[@]}" "${html_files[@]}" "${github_files[@]}"
do
	info "  $file"
	if [[ -z $NOOP ]]
	then
		sed -e "s?REPO_NAME?$repo_name?g" \
		    -e "s?MICROSITE_TITLE?$microsite_title?g" \
		    -e "s?MICROSITE_DESCRIPTION?$microsite_description?g" \
		    -e "s?DASHBOARD_URL?$dashboard_url?g" \
		    -e "s?DASHBOARD?$dashboard?g" \
		    -e "s?PUBLISH_BRANCH?$publish_branch?g" \
		    -e "s?ASSIGNEES?$assignees?g" \
		    -e "s?YMD_TSTAMP?$ymdtimestamp?g" \
		    -e "s?TIMESTAMP?$timestamp?g" \
		    -i ".back" "$file"
	else
		$NOOP sed ... -i .back $file
	fi
done

info "Delete the backup '*.back' files that were just made."
$NOOP find . -name '*.back' -exec rm {} \;

info "Committing changes to the work branch: $work_branch."
# Use --no-verify to suppress complaints and nonzero exit when
# there is nothing to commit.
$NOOP git commit --no-verify -m "$0: Committing changes after variable substitution." .

if [[ $work_branch != $publish_branch ]]
then
	exists=$(git br -a | grep $publish_branch | wc -l)
	if [[ $exists -eq 0 ]]
	then
		info "Create a $publish_branch branch, from which the website will be published."
		$NOOP git checkout -b $publish_branch
	else
		info "Merge the changes to the '$publish_branch' branch, from which the website will be published."
		$NOOP git checkout $publish_branch
		$NOOP git merge main
		$NOOP git commit --no-verify -m "$0: Updating the publication branch, $publish_branch, from the work branch, $work_branch" .
	fi

	info "Switching back to the $work_branch branch."
	$NOOP git checkout $work_branch
fi

if $do_push
then 
	info "Pushing all changes upstream to the GitHub repo."
	$NOOP git push --all
	[[ $status -eq 0 ]] || warn "I could not push the changes back to GitHub." "Try 'git push -all' yourself." "If that doesn't work, talk one of the Alliance engineers for help."
else
	info "You used the --no-push option; changes are not NOT pushed upstream to the GitHub repo!"
	info "You will need to run 'git push --all' yourself!"
fi

echo
info "Done! The current working directory is $PWD."
next_steps $repo_name
