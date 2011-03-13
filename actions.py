from bunch import Bunch
def ANY_cd( root, cd, avatar ):
    return Bunch.resolve( cd.bunch )

def ANY_ls( root, ls, avatar ):
    return Bunch.resolve( ls.bunch )

def ANY_rm( root, rm, avatar ): 
    Bunch.resolve( rm.bunch ).delete()
    return Bunch.resolve( rm.bunch )

def ANY_send( root, send, avatar ):
    return "<script>alert('%s');</script>" % send.bunch
