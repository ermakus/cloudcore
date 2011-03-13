from bunch import Bunch, ROOT_SYS
def ANY_cd( root, cd, avatar ):
    return Bunch.resolve( cd.bunch )

def ANY_ls( root, ls, avatar ):
    return Bunch( ROOT_SYS + "/result", "message", '\r\n'.join( x.ls() for x in ls.children() ) )

def ANY_rm( root, rm, avatar ): 
    for child in rm.children():
        child.delete()
    return Bunch( ROOT_SYS + "/result", "message", "Deleted %s" % rm.bunch  )

def ANY_send( root, send, avatar ):
    return "<script>alert('%s');</script>" % send.bunch
