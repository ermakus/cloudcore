from bunch import Bunch, ROOT_SYS
import unittest
from tests import all_tests
import getopt

def get_opts( cli ):
    opt, val  = getopt.getopt(cli.split(), 'l:t:',['level=','template='])
    level = 2
    template = None
    for o, a in opt:
        if o in ('-l','--level'): level = int(a)
        if o in ('-t','--template'): template = a
    return {'level':level, 'template':template}

def invalid( cmd, avatar ):
    return Bunch( ROOT_SYS + "error/invalid","error",cmd.kind + " " + cmd.bunch)
 
def render( render, avatar ):
    opt = get_opts( render.bunch )
    return ''.join( x.render( level=opt['level'], template=opt['template'] ) for x in render.children() )

def ls( ls, avatar ):
    return ''.join( x.ls( get_opts( ls.bunch )['level'] ) for x in ls.children() )

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
