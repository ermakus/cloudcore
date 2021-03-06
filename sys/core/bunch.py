from simplejson import dumps, loads
import random, string, os
import magic, mimetypes
from config import *
from jinja2 import Environment, Template, FunctionLoader
from store import RedisStore, FileStore

def recursive(f,none=""):
    """ 
    Decorator: Limit recursuve call to 'level' and prevent circular refs 
    """
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


CACHE = {'#':'Dummy Cache'}
#CACHE = False

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

        return "%s: %s" % ( self.name(), bunch)

    def xid(self):
        return self.path.replace(SEPARATOR,'_')
 
    def name(self):
        return os.path.basename( self.path )

    def fname(self):
        return ROOT_DIR + self.path

    @recursive
    def ls(self, level=1, ident=0, hist=None):
        offset = ''.join('    ' for i in xrange( ident ) ) + str(self)
        if level > 1:
            offset += ''.join( '\n' + x.ls(level=level-1,ident=ident+1,hist=hist) for x in self.children()).rstrip('\n')
        return offset
 
    def save(self,storage="redis"):
        for store in self.store: 
            if store.name in storage:
                store.save( self )

        p = self.parent()
        if p:
            p.attach( self )
            p.save()

    @recursive
    def delete(self, storage="redis", hist=None):

        if CACHE and self.path in CACHE: del CACHE[ self.path ]
 
        for ch in self.children():
            ch.delete( hist=hist )

        p = self.parent()
        if p: 
            p.detach( self )

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
        return Bunch.resolve( os.path.dirname( self.path ) )

    def children(self):
        children = []
        for store in self.store:
            children.extend( x for x in store.relations(self) if x not in children )
        children.sort()
        return [Bunch.resolve( path ) for path in children]

    def children_count(self):
        return len( self.children() )

    def attach(self,bunch):
        for store in self.store:
            store.relations( self ).add( bunch.path )
 
    def detach(self,bunch):
        for store in self.store: 
            store.relations( self ).remove( bunch.path )

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
            temp = Bunch.resolve( TEMPLATES + kind + ".template", "template", "{% autoescape false %}{{ bunch.bunch }}{% endautoescape %}" )
            return temp.bunch

        env = Environment(autoescape=True, loader=FunctionLoader( load ), extensions=['jinja2.ext.autoescape'])
        return env.get_template( template ).render( bunch=self, level=level-1, template=template )

    def execute(self,avatar=None):

        import actions

        try:
            return getattr(actions,self.kind)(self, avatar)
        except AttributeError:
            return getattr(actions,"invalid")(self, avatar)
   
    def mimetype(self):
        if self.mime: return self.mime
        self.mime, encoding = mimetypes.guess_type( self.name() )        
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
    def connect(self,db=0):
        self.store = [ 
		RedisStore( db ), FileStore( ROOT_DIR ) 
	]

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
        if CACHE and path in CACHE: return CACHE[ path ]

        # If not a path, try to parse as command and put in log
        if SEPARATOR != path[0]: 
	    return self.parse( path=self.uniq( ROOT_SYS + "log" ).path ,kind=kind, cmd=path )

        # Root is hardcoded here
        if path == SEPARATOR: 
            bunch = Bunch( SEPARATOR, GHOST, "The root" )
        else:
            bunch = Bunch( path, kind, bnc )

        if Bunch.exists( path ):
            for store in self.store:
                if store.load( bunch ) and store.name == "file":
		    bunch.save("redis")
        else:
            bunch.save()

        if CACHE: CACHE[ bunch.path ] = bunch

        return bunch

    @classmethod
    def uniq(self, path, kind=GHOST,txt=None):
	if path[-1] != SEPARATOR:
            path += SEPARATOR
        while True:
            uid = path + ''.join(random.choice(string.letters) for i in xrange(8))
            if not Bunch.exists( uid ):
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
        bunch = Bunch.resolve(path)
        bunch.kind = cmd
        bunch.bunch =' '.join(parts[1:]) 
        for p in parts[1:]:
            if p[0] == SEPARATOR:
                bunch.attach( Bunch.resolve( p ) )
        bunch.save()
        if CACHE: CACHE[ bunch.path ] = bunch
        return bunch

_ = Bunch.resolve
