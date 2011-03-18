import redis
from redis.wrap import *
from simplejson import dumps, loads
import random, string, os
import magic, mimetypes
from config import *
from jinja2 import Environment, Template, FunctionLoader

""" Decorator: Limit recursuve call to 'level' and prevent circular refs """
def recursive(f,none=""):
    def wrapped(*args,**kwds):
        _self = args[0]
        if 'hist' in kwds:
            if _self.path in kwds['hist']: 
                return none
        else:
            kwds['hist'] = []
        kwds['hist'] += [ _self.path ]
        
        if 'level' in kwds and kwds['level'] == 0:
            return none
        else:
            return f(*args,**kwds)
    return wrapped


class RedisStore:
    """
    Redis noSQL object storage
    """
    name = "default"

    def __init__(self, context):
        self.context = context
        self.redis   = get_redis(context)

    def __del__(self):
        self.redis.flushdb()

    def save(self, bunch):
        self.redis[ bunch.path ] = bunch.bunch
        self.redis[ bunch.path + "?kind"] = bunch.kind
 
    def load(self, bunch):
        bunch.bunch = self.redis[ bunch.path ]
        bunch.kind  = self.redis[ bunch.path + "?kind" ]

    def delete(self, bunch):
        self.redis.delete( bunch.path  )
        self.redis.delete( bunch.path + "?kind" )
        self.redis.delete( bunch.path + "?links" )

    def exists(self, path):
        return self.redis.exists( path )

    def relations(self, bunch):
        return get_set( bunch.path + "?links", self.context )

class FileStore:
    """
    Redis noSQL object storage
    """
    name = "file"

    def __init__(self, root):
        self.root = root

    def __del__(self):
        pass

    def save(self, bunch):
        fn = bunch.fname()
        dir = os.path.dirname(fn)
        if not os.path.exists(dir):
            os.makedirs(dir)
        f = open( fn, "w" )
        f.write( bunch.bunch )
        f.close()
 
    def load(self, bunch):
        try:
            fp = open( bunch.fname(), "r" )
	    bunch.bunch = fp.read()
            fp.close()
            return True
        except IOError:
            return False
 
    def delete(self, bunch):
        try:
            os.remove( bunch.fname() )
            return True
        except OSError:
            return False

    def exists(self, path):
        return os.path.exists( self.root + path )

    def relations(self, bunch):
        return None


class Bunch:

    def __init__(self,path="/tmp",kind=GHOST,bunch=None):
        self.path = path
        self.kind = kind
        self.bunch = bunch
        self.mime = None
        self.handlers = []

    def __str__(self):

        bunch = self.bunch
        if self.is_binary(): 
            bunch = "[%s]" % self.mimetype()
        else:
            if bunch:
                bunch = bunch.translate(None,'\r\n')
                if len(bunch)>60: bunch = bunch[:60] + ".."

        return "%s.%s: %s" % ( self.name(), self.kind, bunch)

    def xid(self):
        return self.path.replace(SEPARATOR,'_')
 
    def name(self):
        return os.path.basename( self.path )

    def fname(self):
        return ROOT_DIR + self.path + "." + ( self.kind or GHOST )

    @recursive
    def ls(self, level=1, ident=0, hist=None):
        offset = ''.join('    ' for i in xrange( ident ) ) + str(self)
        return offset + ''.join( '\n' + x.ls(level=level-1,ident=ident+1,hist=hist) for x in self.children()).rstrip('\n')
 
    def save(self,storage="default"):
        for store in self.store: 
            if store.name in storage:
                store.save( self )

        p = self.parent()
        if p: p.save()

    @recursive
    def delete(self, storage="default", hist=None):

        for ch in self.children():
            ch.delete( hist=hist )

        p = self.parent()
        if p: p.detach( self )

        for store in self.store:
            if store.name in storage:
                store.delete( self )

    def level(self):
        me = self.parent()
        level = 0
        while me:
            level += 1
            me = me.parent()
        return level
        
    def parent(self):
        if( self.path == SEPARATOR ) or (not self.path): return None
        return Bunch.resolve( os.path.dirname( self.path ), GHOST, None )

    def children(self):
        children = []
        for store in self.store: 
            rels = store.relations(self) 
            if rels:
                for path in rels:
                    children += [ Bunch.resolve( path, GHOST, None ) ]

        return children

    def children_count(self):
        return len( self.children() )

    def attach(self,bunch):
        for store in self.store:
            rels = store.relations( self )
            if rels:
                rels.add( bunch.path )
 
    def detach(self,bunch):
        for store in self.store: 
            rels = store.relations( self )
            if rels:
                rels.remove( bunch.path )

    def json(self, depth=1):
        depth = self.level() + depth
        def encode_tree(obj):           
            if not isinstance(obj, Bunch):
                raise TypeError("%r is not Bunch" % (obj,))         
            d = obj.__dict__.copy()
            if obj.level() < depth:
                d['children'] = obj.children()
            return d

        return dumps( encode_tree(self), default=encode_tree )
  
    @recursive
    def render(self, level=1, hist=None, template=None):
        if template is None: template = self.kind
        def load(kind):
            temp = Bunch.resolve( TEMPLATES + kind, "template", "{% autoescape false %}{{ bunch.bunch }}{% endautoescape %}" )
            return temp.bunch

        env = Environment(autoescape=True, loader=FunctionLoader( load ), extensions=['jinja2.ext.autoescape'])
        result = env.get_template( template ).render( bunch=self, level=level-1, template=template )

        return str(result)

    def execute(self,avatar=None):

        import actions

        try:
            return getattr(actions,self.kind)(self, avatar)
        except AttributeError:
            return getattr(actions,"invalid")(self, avatar)
   
    def mimetype(self):
        if self.mime: return self.mime
        self.mime, encoding = mimetypes.guess_type( self.name() + '.' + self.kind )        
        if not self.mime:
            if self.bunch:
                mime = magic.Magic(mime=True)
                self.mime = mime.from_buffer( self.bunch )
            else:
                self.mime = "text/plain"
        return self.mime

    def is_binary(self):
        if 'text' in self.mimetype():
            return False
        if 'javascript' in self.mimetype():
            return False

        return True

    def subscribe(self, handler):
        self.handlers += [handler]

    def unsubscribe(self, handler):
        self.handlers.remove(handler)

    def notify( self, event ):
        for h in self.handlers:
            h( self, event ) 

    """ Class methods """
 
    @classmethod
    def connect(self,context="default"):
        self.store = [ RedisStore( context ), FileStore( ROOT_DIR ) ]

    @classmethod
    def disconnect(self):
        for store in self.store: del store
        self.store = [] 

    @classmethod
    def exists(self, path):
        for store in self.store:
            if store.exists( path ):
                return True
        return False

    @classmethod
    def resolve(self, path, kind=GHOST,bnc=None):

        # If not a path, try to parse as command and put in history
        if SEPARATOR != path[0]: 
	    return self.parse( path=self.uniq( ROOT_SYS + "log" ).path ,kind=kind, cmd=path )

        # Root is hardcoded here
        if path == SEPARATOR: 
            return Bunch( SEPARATOR, GHOST, "The root" )

        bunch = Bunch(path, kind, bnc)

        if self.exists( path ):
            for store in self.store:
                store.load( bunch )
        else:
	    # Create new 'Ghost' object
            p = bunch.parent()
            if p: p.attach( bunch )
            bunch.save()

        return bunch

    @classmethod
    def uniq(self, path, kind=GHOST,txt=None):
	if path[-1] != SEPARATOR:
            path += SEPARATOR
        while True:
            uid = path + ''.join(random.choice(string.letters) for i in xrange(8))
            if not self.exists( uid ):
                return Bunch.resolve( uid, kind, txt )

    @classmethod
    def read(self, src):
        if isinstance(src,str):
            src = loads( src )
        return Bunch( src["path"], src["kind"], src["bunch"] )

    @classmethod
    def parse(self, path, kind=GHOST, cmd="nop"):
        parts = cmd.strip().split()
        cmd = parts[0]
        bunch = Bunch(path,cmd,' '.join(parts[1:]))
        for p in parts[1:]:
            if p[0] == SEPARATOR:
                bunch.attach( Bunch.resolve( p ) )
        bunch.save()
        return bunch

_ = Bunch.resolve
