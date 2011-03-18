#
# Engine configuration
#
VERSION     = "0.1-dev"
ROOT        = SEPARATOR = '/'
ROOT_SYS    = ROOT + 'sys' + SEPARATOR
LINKS       = ROOT_SYS + 'links'
TEMPLATES   = ROOT_SYS + 'templates' + SEPARATOR
MEDIA       = ROOT_SYS + 'media' + SEPARATOR
INTERFACE   = "0.0.0.0"
STATIC_PORT = 8000
STOMP_PORT  = 9999

import os, sys
ROOT_DIR    = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
SYS_DIR     = ROOT_DIR + ROOT_SYS
LOG_DIR     = SYS_DIR + "log"  + SEPARATOR
CORE_DIR    = SYS_DIR + "core" + SEPARATOR

sys.path.append( SYS_DIR )
sys.path.append( CORE_DIR )

GHOST = "dir"

print "Cloud core version: %s root: %s" % ( VERSION, CORE_DIR )
