#!/usr/bin/env zsh
#---------------------------------------------------------------------------
# Checks that all external links, those starting with http*, have "targets".
#---------------------------------------------------------------------------

default_path="docs"

help() {
	cat << EOF
A fairly crude, but mostly effective tool that checks URLs in markdown
files and HTML template files to make sure they all have "targets". 
For markdown files, it prints anchor tags ("[name](url)") that don't
have a "{:target=...}" appended to them. For HTML files, it looks for 
the equivalent "<a href="..." target="...">...</a>".

It also handles two '{{site.*url}}' definitions we use for referencing 
commonly used external sites:
* '{{site.glossaryurl}}' for the separate glossary site.
* '{{site.gh_edit_repository}}' for the GitHub repo URL.

It attempts to correctly ignore image URLs, e.g., '![label](https://example.com/image.png)',
by looking at the file extension (jpg|jpeg|png|svg|mp3|mp4). This means
that if a URL that should have a target happens to have one of those strings,
it won't be checked for the target!

It doesn't exit with an error if such links are found, because in some
cases, this might be intentional.

Usage: $script [-h|--help] [-n|--noop] [-v|--verbose] [path1 ...]

Where the arguments are the following:
-h | --help            Print this message and exit
-n | --noop            Just print the commands but don't make changes.
-v | --verbose         Print the paths as they are processed. Mostly useful
                       when no problems are found and you are paranoid nothing
                       was checked. ;)
path1 ...              Check these paths. Directories will be visited recursively.
                       Default: All markdown and HTML files under "$default_path",
                       excluding files under "_site" and "_sass".
NOTES:
1. Skips files found under "temp", "tmp", "_site", and "_sass" directories.
EOF
}

error() {
	for arg in "$@"
	do
		echo "ERROR: $arg"
	done
	help
	exit 1
}

paths=()
: ${VERBOSE=}
while [[ $# -gt 0 ]]
do
	case $1 in
		-h|--h*)
			help
			exit 0
			;;
		-n|--n*)
			NOOP=echo
			;;
		-v|--v*)
			VERBOSE=echo
			;;
		-*)
			error "Unrecognized option: $1"
			;;
		*)
			paths+=("$1")
			;;
	esac
	shift
done

[[ ${#paths[@]} -gt 0 ]] || paths=("$default_path")

eg=$(which egrep)
# Use a somewhat complicated script to find the URLs starting
# with http, print only the matches and then filter out the 
# URLs that contain "target". It won't work perfectly, but ...
[[ -n "$VERBOSE" ]] && echo "Checking markdown files:"
for path in "${paths[@]}"
do
	if [[ -n "$VERBOSE" ]]
	then
		dir=$([[ -d "$path" ]] && echo "(directory)")
		echo "$path $dir"
	fi
	$NOOP $eg -nHoR '\(https?[^)]+\)(\S*)' \
		--include '*.markdown' --include '*.md' \
 		--exclude-dir 'temp' --exclude-dir 'tmp' \
		--exclude-dir '_site' --exclude-dir '_sass' \
		$path | $eg -v 'target=' | $eg -v '\.(jpg|jpeg|png|svg|mp3|mp4)'
	$NOOP $eg -nHoR '\(\{\{site.glossaryurl\}\}[^)]*\)(\S*)' \
		--include '*.markdown' --include '*.md' \
 		--exclude-dir 'temp' --exclude-dir 'tmp' \
		--exclude-dir '_site' --exclude-dir '_sass' \
		$path | $eg -v 'target=' | $eg -v '\.(jpg|jpeg|png|svg|mp3|mp4)'
	$NOOP $eg -nHoR '\(\{\{site.gh_edit_repository\}\}[^)]*\)(\S*)' \
		--include '*.markdown' --include '*.md' \
 		--exclude-dir 'temp' --exclude-dir 'tmp' \
		--exclude-dir '_site' --exclude-dir '_sass' \
		$path | $eg -v 'target=' | $eg -v '\.(jpg|jpeg|png|svg|mp3|mp4)'
done

[[ -n "$VERBOSE" ]] && echo "Checking HTML files:"
for path in "${paths[@]}"
do
	if [[ -n "$VERBOSE" ]]
	then
		dir=$([[ -d "$path" ]] && echo "(directory)")
		echo "$path $dir"
	fi
	$NOOP $eg -nHoR '<a\s*href="https?[^>]+>' \
		--include '*.html' \
 		--exclude-dir 'temp' --exclude-dir 'tmp' \
		--exclude-dir '_site' --exclude-dir '_sass' \
		$path | $eg -v 'target=' | $eg -v '\.(jpg|jpeg|png|svg|mp3|mp4)'
done
