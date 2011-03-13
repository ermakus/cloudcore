import redis
from redis.wrap import *
from simplejson import dumps, loads
import random, string, os

from jinja2 import Environment, Template, FunctionLoader

GHOST     = 'ghost'
ROOT      = SEPARATOR = '/'
ROOT_SYS  = ROOT + 'sys' + SEPARATOR
TEMPLATES = ROOT_SYS + 'templates' + SEPARATOR
LINKS     = ROOT_SYS + 'links' + SEPARATOR

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'root'))


""" Bunch! The Father Of All Objects """


class Bunch:

    def __init__(self,path="/tmp",kind=GHOST,bunch=None):
        if SEPARATOR != path[0]: raise Exception("Invalid path: " + path)
        self.path = path
        self.kind = kind
        self.bunch = bunch

    def __unicode__(self):
        return self.fname()

    def __str__(self):
        return self.__unicode__()

    def xid(self):
        return self.path.replace(SEPARATOR,'_')
 
    def name(self):
        return os.path.basename( self.path )

    def fname(self):
        return ROOT_DIR + self.path + "." + self.kind

    def dump(self, ident=0):
        offset = ''.join('    ' for i in xrange( ident ) )
        print offset + self.__str__()
        for bunch in self.children():
            bunch.dump(ident+1)
 
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
            os.remove( self.fname() )

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

        env = Environment(autoescape=True, loader=FunctionLoader( load ), extensions=['jinja2.ext.autoescape'])
        return env.get_template( self.kind ).render( bunch=self, depth=depth-1, MEDIA_URL='/sys/media/' )

    def execute(self,target=None, avatar=None):

        if target is None:
            target = self

        cmd1 = self.kind + "_" + target.kind
        cmd2 = "ANY_" + target.kind

        import actions

        try:
            return getattr(actions,cmd1)(self, target, avatar)
        except AttributeError:
            try:
                return getattr(actions,cmd2)(self, target, avatar)
            except AttributeError:
                return None

    """ Class methods """
 
    @classmethod
    def connect(self,system):
        self.system = system
        self.db = get_redis(system )

    @classmethod
    def disconnect(self):
        if( self.db ):
            self.db.flushdb()
            self.db = None

    @classmethod
    def resolve(self, path, kind=GHOST,bnc=None):

        if path == SEPARATOR: 
            return Bunch( SEPARATOR, "root", "The Root")

        if self.db.exists( path ):
            bunch = Bunch(path, self.db[ path + "?kind" ], self.db[ path ])
            try:
                fp = open( bunch.fname(), "r" )
	        bunch.bunch = fp.read()
                fp.close()
            except IOError:
                pass

        else:
            bunch = Bunch(path, kind, bnc)
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
            if not self.db.exists( uid ):
                return Bunch.resolve( uid, kind, txt )

    @classmethod
    def read(self, src):
        if isinstance(src,str):
            src = loads( src )
        return Bunch( src["path"], src["kind"], src["bunch"] )

    @classmethod
    def parse(self, path, cmd):
        parts = cmd.strip().split()
        if parts[0][0] == '!':
            cmd = parts[0][1:]
            bunch = Bunch(path,cmd,' '.join(parts[1:]))
            for p in parts[1:]:
                if p[0] == SEPARATOR:
                    bunch.attach( Bunch.resolve( p ) )
        else:
            bunch = Bunch(path,"text",cmd)
 
        bunch.save()
        return bunch
