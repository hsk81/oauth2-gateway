#!/bin/bash

###############################################################################
###############################################################################

# Initial $ ./setup.sh init

###############################################################################
###############################################################################

ACTMETH=${1}
APPNAME=${2-"oag"}

###############################################################################
###############################################################################

function setup_env () {
    if [ $VIRTUAL_ENV ] ; then
        exit 0
    else
        git submodule update --init --recursive
        if [ $PY3 ] ; then
            virtualenv3 . --prompt="[$1] " ## --system-site-packages
        else
        if [ $PY2 ] ; then
            virtualenv2 . --prompt="[$1] " ## --system-site-packages
        else
            virtualenv  . --prompt="[$1] " ## --system-site-packages
        fi
        fi
    fi
}

function clean_env () {
    rm -rf bin/ include/ lib/ share/
}

function clean_egg () {
    rm -rf build/ dist/ *.egg-info/
}

function clean_pip () {
    rm -rf pip-selfcheck.json
}

function clean_pyc () {
    rm -rf $(tree -fi | grep \\.pyc$)
    rm -rf $(tree -fi | grep __pycache__$)
}

function clean_log () {
    rm -rf $(tree -fi | grep \\.log$)
}

###############################################################################
###############################################################################

case $ACTMETH in
    clean)
        clean_env && \
        clean_egg && \
        clean_pip && \
        clean_pyc && \
        clean_log ;;
    clean-env)
        clean_env ;;
    clean-egg)
        clean_egg ;;
    clean-pip)
        clean_pip ;;
    clean-pyc)
        clean_pyc ;;
    clean-log)
        clean_log ;;
    init)
        setup_env $APPNAME ;;
    *)
        $0 init $1 $2 ;;
esac

###############################################################################
###############################################################################

exit 0
