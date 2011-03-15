import redis
from redis.wrap import *
from simplejson import dumps, loads
import random, string, os
import magic, mimetypes

from jinja2 import Environment, Template, FunctionLoader

GHOST     = 'ghost'
ROOT      = SEPARATOR = '/'
ROOT_SYS  = ROOT + 'sys' + SEPARATOR
TEMPLATES = ROOT_SYS + 'templates' + SEPARATOR
LINKS     = ROOT_SYS + 'links' + SEPARATOR
MEDIA     = ROOT_SYS + 'media' + SEPARATOR
COMET     = "http://localhost:9999"

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'root'))
TEXT_CHARS = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))


""" Bunch! The Mega Object """


class Bunch:

    def __init__(self,path="/tmp",kind=GHOST,bunch=None):
        self.path = path
        self.kind = kind
        self.bunch = bunch
        self.mime = None

    def __str__(self):

        bunch = self.bunch

        if bunch:
            if self.is_binary(): 
                bunch = "[BINARY, %s]" % self.mimetype()
            else:
                if len(bunch)>60: bunch = bunch[:60] + ".."
                bunch = bunch.translate(None,'\r\n')

        return "%s.%s: %s" % ( self.name(), self.kind, bunch)

    def xid(self):
        return self.path.replace(SEPARATOR,'_')
 
    def name(self):
        return os.path.basename( self.path )

    def fname(self):
        return ROOT_DIR + self.path + "." + self.kind

    def ls(self, level=1, ident=0, hist=None):


        hist = hist or []
        offset = ''.join('    ' for i in xrange( ident ) )

        if self.path in hist: 
            return offset + "[DUP] " + str(self)

        hist += [self.path]

        offset += str(self) 

        if level > 0:
            for x in self.children():
                offset += ('\r\n' + x.ls(level-1,ident+1,hist))

        return offset
 
    def save(self,storage="default"):
        self.db[ self.path ] = self.bunch
        self.db[ self.path + "?kind"] = self.kind
        if storage == "file":
            fn = self.fname()
            dir = os.path.dirname(fn)
            if not os.path.exists(dir):
                os.makedirs(dir)
            f = open( fn, "w" )
            f.write( self.bunch )
            f.close()

        p = self.parent()
        if p: p.save()

    def delete(self, storage="default", hist=None):
        hist = hist or []
        if self.path in hist: 
            return
        hist += [self.path]

        for ch in self.children():
            ch.delete( hist=hist )

        p = self.parent()
        if p: p.detach( self )

        self.db.delete( self.path  )
        self.db.delete( self.path + "?kind" )
        self.db.delete( LINKS + self.path )

        if storage == "file":
            try:
                os.remove( self.fname() )
            except OSError:
                pass

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
        for path in get_set( LINKS + self.path, self.system ):
            children += [ Bunch.resolve( path ) ]
        return children

    def attach(self,bunch):
        edges = get_set( LINKS + self.path, system=self.system )
        edges.add( bunch.path )
 
    def detach(self,bunch):
        edges = get_set( LINKS + self.path, system=self.system )
        if bunch.path in edges:
            edges.remove( bunch.path )

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
  
    def render(self, depth=1):

        def load(kind):
            temp = Bunch.resolve( TEMPLATES + kind, "template", "{% autoescape false %}{{ bunch.bunch }}{% endautoescape %}" )
            return temp.bunch

        result = ""
        if depth > 0:  
            env = Environment(autoescape=True, loader=FunctionLoader( load ), extensions=['jinja2.ext.autoescape'])
            result = env.get_template( self.kind ).render( bunch=self, depth=depth-1, MEDIA=MEDIA, COMET=COMET )

        return str(result)

    def execute(self,target=None, avatar=None):

        if target is None:
            target = self

        cmd1 = self.kind + "_" + target.kind
        cmd2 = "ANY_" + self.kind

        import actions

        try:
            return getattr(actions,cmd1)(self, target, avatar)
        except AttributeError:
            try:
                return getattr(actions,cmd2)(self, target, avatar)
            except AttributeError:
                return Bunch( ROOT_SYS + "/error", "error", "No handler for %s" % self.kind )
   
    def mimetype(self):
        if self.mime: return self.mime
        self.mime, encoding = mimetypes.guess_type( self.name() + '.' + self.kind )
        if not self.mime:
            mime = magic.Magic(mime=True)
            self.mime = mime.from_buffer( self.bunch )
        return self.mime

    def is_binary(self):
        if 'text' in self.mimetype():
            return False

        return True

    """ Class methods """
 
    @classmethod
    def connect(self,system="default"):
        self.system = system
        self.db = get_redis(system)

    @classmethod
    def disconnect(self):
        if( self.db ):
            self.db.flushdb()
            self.db = None

    @classmethod
    def resolve(self, path, kind=GHOST,bnc=None):

        # If not a path, try to parse as command and put in history
        if SEPARATOR != path[0]: 
	    return self.parse( path=self.uniq( ROOT_SYS + "log" ).path ,kind=kind, cmd=path )

        # Root is hardcoded here
        if path == SEPARATOR: 
            return Bunch( SEPARATOR, "root", "The Root")

        # Check in redis or load from file
        if self.db.exists( path ):
            bunch = Bunch(path, self.db[ path + "?kind" ], self.db[ path ])
        else:
	    # Create new 'Ghost' object
            bunch = Bunch(path, kind, bnc)
            p = bunch.parent()
            if p: p.attach( bunch )
            bunch.save()

        try:
            fp = open( bunch.fname(), "r" )
	    bunch.bunch = fp.read()
            fp.close()
        except IOError:
            pass
 
        return bunch

    @classmethod
    def uniq(self, path, kind=GHOST,txt=None):
	if path[-1] != SEPARATOR:
            path += SEPARATOR
        while True:
            uid = path + ''.join(random.choice(string.letters) for i in xrange(8))
            if not self.db.exists( uid ):
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
