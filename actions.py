from bunch import Bunch, ROOT_SYS
import unittest
from tests import all_tests

def ANY_render( root, render, avatar ):
    return '\r\n'.join( x.render(1) for x in render.children() )

def ANY_ls( root, ls, avatar ):
    return '\r\n'.join( x.ls(1) for x in ls.children() )

def ANY_rm( root, rm, avatar ): 
    for child in rm.children():
        child.delete()
    return  "Deleted %s" % rm

def ANY_send( root, send, avatar ):
    return "<script>alert('%s');</script>" % send.bunch

def ANY_test( root, send, avatar ):
    tests = all_tests()
    return unittest.TextTestRunner().run(tests)
