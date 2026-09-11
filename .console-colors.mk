# console-colors.mk

# Color definitions for highlighting console output.
# These definitions work on MacOS and Linux, zsh and bourne/dash shells.
# Adapted from https://stackoverflow.com/a/53528374
# Posted by Robert Ranjan
# Retrieved 2026-05-18, License - CC BY-SA 4.0
# TIP: Run `make show-colors` (This target is at the end of this file.)

# We get a lot of error calling tput in the GitHub CI headless linux servers, so
# if TERM isn't defined, make all the "core" definitions empty:
ifeq (${TERM},)
RED =
GREEN =
ORANGE =
BLUE =
PINK =
DARK_GREEN =
LIGHT_GREY =
BLACK =
# virtually identical to RED:
RED2 =
BOLD =
_END_BOLD =
_END =
else
# Where you see 'echo ""' or 'echo " "' commands, those add white space
# just after the beginning or just before the end of bold strings, for
# a better appearance. Yes, one is " " and the other is "". That was
# determined through trial and error...
RED        = $(shell tput setaf 1)
GREEN      = $(shell tput setaf 2)
ORANGE     = $(shell tput setaf 3)
BLUE       = $(shell tput setaf 4)
PINK       = $(shell tput setaf 5)
DARK_GREEN = $(shell tput setaf 6)
LIGHT_GREY = $(shell tput setaf 7)
BLACK      = $(shell tput setaf 8)
# virtually identical to RED:
RED2       = $(shell tput setaf 9)
BOLD       = $(shell tput smso; echo " ")
_END_BOLD  = $(shell echo ""; tput rmso)
_END       = $(shell tput sgr0; tput rmso)
endif
# Note the definitions with labels, like "ERROR:" have a trailing white space 
# which both separate the label from the messages when used and also have the labels
# line up equally! Use "make show-colors" to see this.
# Note that when BOLD is used, it reverses foreground and background. We add a space
# before the text and one should be added afterwards, for a less "cut off" appearance.
# The empty '#' comments force a particular amount of white space at the end of the
# definition, when needed for ideal alignment.
ERROR        = ${RED}${BOLD}ERROR:  #
WARN         = ${ORANGE}WARNING: #
WARNING      = ${ORANGE}WARNING: #
NOTE         = ${GREEN}NOTE:    #
INFO         = ${DARK_GREEN}INFO:    #
TIP          = ${PINK}TIP:     #
HIGHLIGHT    = ${BLUE}${BOLD}

# "Labels" for when you just want to, e.g., "ERROR:" colored, but the rest of the line should be "normal".
# No "${_END}" has to be provided when these labels are used.

ERROR_LABEL     = ${RED}${BOLD}ERROR:${_END_BOLD}   ${_END}
WARN_LABEL      = ${ORANGE}${BOLD}WARNING:${_END_BOLD} ${_END}
WARNING_LABEL   = ${ORANGE}${BOLD}WARNING:${_END_BOLD} ${_END}
NOTE_LABEL      = ${GREEN}${BOLD}NOTE:${_END_BOLD}    ${_END}
INFO_LABEL      = ${DARK_GREEN}${BOLD}INFO:${_END_BOLD}    ${_END}
TIP_LABEL       = ${PINK}${BOLD}TIP:${_END_BOLD}     ${_END}

# For "special" strings in output:
CODE            = ${DARK_GREEN}

.PHONY: show-colors

# Use this target to see the colors defined above.
show-colors::
	$(info This is how the color and message definition look using $$(info ...) and related output functions:)
	$(info Note that when BOLD is used, it reverses foreground and background. We add a space before and after the text.)
	$(info This is <${RED}RED${_END}>)
	$(info This is <${RED2}RED2${_END}>)
	$(info This is <${GREEN}GREEN${_END}>)
	$(info This is <${ORANGE}ORANGE${_END}>)
	$(info This is <${BLUE}BLUE${_END}>)
	$(info This is <${PINK}PINK${_END}>)
	$(info This is <${DARK_GREEN}DARK_GREEN${_END}>)
	$(info This is <${LIGHT_GREY}LIGHT_GREY${_END}>)
	$(info This is <${BLACK}BLACK${_END}>)
	$(info This is <${BLACK}${BOLD}BLACK and BOLD${_END_BOLD}${_END}>)
	$(info This is <${PINK}PINK mixed with ${BOLD}BOLD${_END_BOLD} text${_END}>)
	$(info )
	$(info This is an ERROR:     ${ERROR}Oooops!${_END_BOLD}${_END})
	$(info This is a  WARN:      ${WARN}Careful!${_END})
	$(info This is a  WARNING:   ${WARNING}Careful!${_END})
	$(info This is a  NOTE:      ${NOTE}Of note...${_END})
	$(info This is an INFO:      ${INFO}It's useful to know${_END})
	$(info This is a  TIP:       ${TIP}This can help...${_END})
	$(info This is a  HIGHLIGHT: ${HIGHLIGHT}/foo/bar/baz${_END_BOLD}${_END})
	$(info )
	$(info This is an ERROR_LABEL:     ${ERROR_LABEL}Oooops!)
	$(info This is a  WARN_LABEL:      ${WARN_LABEL}Careful!)
	$(info This is a  WARNING_LABEL:   ${WARNING_LABEL}Careful!)
	$(info This is a  NOTE_LABEL:      ${NOTE_LABEL}Of note...)
	$(info This is an INFO_LABEL:      ${INFO_LABEL}It's useful to know)
	$(info This is a  TIP_LABEL:       ${TIP_LABEL}This can help...)
	$(info (There isn't a 'HIGHLIGHT_LABEL', because it would be empty!))
	@echo  # using echo suppresses "nothing to be done ..." messages.
