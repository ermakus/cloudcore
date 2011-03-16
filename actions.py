from bunch import Bunch, ROOT_SYS
import unittest
from tests import all_tests
import getopt

def get_level( cli ):
    opt, val  = getopt.getopt(cli.split(), 'l:',['level='])
    level = 2
    for o, a in opt:
        if o in ('-l','--level'): level = int(a)
    return level
 
def render( render, avatar ):
    template = None
    return ''.join( x.render( level=get_level( render.bunch ), template=template ) for x in render.children() )

def ls( ls, avatar ):
    return ''.join( x.ls( get_level( ls.bunch ) ) for x in ls.children() )

def rm( rm, avatar ):
    child = rm.children()[0]
    child.delete()
    return  """<delete id="%s"/>""" % child.xid()

def alert( send, avatar ):
    return "<script>alert('%s');</script>" % send.bunch

def test( test, avatar ):
    tests = all_tests()
    return unittest.TextTestRunner().run(tests)

def stress( cmd, avatar ):
    for x in range(10000):
        b = Bunch.uniq("/tmp/stress","stress","Wow!")
        b.save()
    Bunch.resolve("/tmp/stress").delete()
