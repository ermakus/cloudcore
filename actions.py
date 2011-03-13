from bunch import Bunch, ROOT_SYS
def ANY_render( root, render, avatar ):
    return '\r\n'.join( x.render() for x in render.children() )

def ANY_ls( root, ls, avatar ):
    return '\r\n'.join( x.ls() for x in ls.children() )

def ANY_rm( root, rm, avatar ): 
    for child in rm.children():
        child.delete()
    return  "Deleted %s" % rm

def ANY_send( root, send, avatar ):
    return "<script>alert('%s');</script>" % send.bunch
