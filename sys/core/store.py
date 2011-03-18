import redis
import os

class RedisSet:
    """
    Redis set wrapper
    """
    def __init__(self, name, redis):
        self.name = name
        self.redis = redis

    def add(self, item):
        self.redis.sadd(self.name, item)

    def remove(self, item):
        self.redis.srem(self.name, item)

    def pop(self, item):
        return self.redis.spop(self.name, item)

    def __iter__(self):
        for item in self.redis.smembers(self.name):
            yield item

    def __len__(self):
        return len(self.redis.smembers(self.name))

    def __contains__(self, item):
        return self.redis.sismember(self.name, item)

class RedisStore:
    """
    Redis noSQL object storage
    """
    name = "redis"

    def __init__(self, db):
        self.redis   = redis.Redis(host='localhost', port=6379, db=db)

    def __del__(self):
        pass

    def save(self, bunch):
        pipe = self.redis.pipeline()
        pipe.set( bunch.path, bunch.bunch).set(  bunch.path + "?kind", bunch.kind)
        pipe.execute()
 
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
        return RedisSet( bunch.path + "?links", self.redis )

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
        return False #os.path.exists( self.root + path )

    def relations(self, bunch):
        class NopeSet:
            def add(self, item):
                pass

            def remove(self, item):
                pass

            def __iter__(self):
                return iter([])

        return NopeSet()


