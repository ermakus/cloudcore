from bunch import Bunch, GHOST, TEMPLATES, SEPARATOR, ROOT_DIR, ROOT_SYS, CACHE, _
import unittest, os
from json import loads

TEST_PATH="/sys/test"
TEST_DB = 0

class BunchTestCase(unittest.TestCase):
    def setUp(self):
        Bunch.connect( TEST_DB )
        Bunch.resolve( TEST_PATH ).delete()

    def tearDown(self):
        Bunch.resolve( TEST_PATH ).delete()
        self.assertEquals( len( Bunch.store[0].redis.keys( TEST_PATH + "*" ) ), 0 )
        Bunch.disconnect()

    def test_redis(self):
        self.assertTrue( Bunch.store != None )

    def test_resolve(self):
        bunch = Bunch.resolve( TEST_PATH, "test","Test")
        self.assertEquals( bunch.path, TEST_PATH )
        self.assertEquals( bunch.kind, "test" )
        self.assertEquals( bunch.bunch, "Test" )
        bunch = Bunch.resolve( TEST_PATH )
        self.assertEquals( bunch.path, TEST_PATH )
        self.assertEquals( bunch.kind, "test" )
        self.assertEquals( bunch.bunch, "Test" )
 
    def test_delete(self):
        bunch = Bunch.resolve( TEST_PATH, "test","Test")
        self.assertEquals( bunch.kind, 'test' )
        bunch.delete()
        ghost = Bunch.resolve( TEST_PATH )
        self.assertTrue( ghost.kind == GHOST )

    def test_children(self):
        root = Bunch( TEST_PATH, "test", "Test" )
        root.save()
        root.attach( Bunch( TEST_PATH + "/child1","test","Children 1") )
        root.attach( Bunch( TEST_PATH + "/child2","test","Children 2") )
        self.assertTrue( len(root.children()) == 2 )
        self.assertTrue( len(Bunch.resolve(TEST_PATH).children()) == 2 )
        root.detach( Bunch( TEST_PATH + "/child1","test","Not important") )
        self.assertTrue( len(root.children()) == 1 )
        root.delete()
        self.assertTrue( len(root.children()) == 0 )
        c1 = Bunch.resolve( TEST_PATH + "/child1" )
        self.assertEquals( c1.kind, GHOST )
        c1.delete()

    def test_parent(self):
        one = Bunch.resolve( TEST_PATH )
        self.assertEquals( one.parent().path , "/sys" )
        self.assertEquals( one.parent().parent().path, "/" )
        self.assertEquals( one.parent().parent().kind, GHOST )
        self.assertEquals( one.parent().parent().parent(), None )
        two = Bunch.resolve( TEST_PATH + "/two" )
        self.assertEquals( one.path, two.parent().path )
        self.assertEquals( len( one.children() ), 1 )

    def test_json(self):
        root = Bunch.resolve( TEST_PATH, "test", "Test" )
        self.assertEquals( len(root.children()), 0 )
        child = Bunch.resolve( TEST_PATH + "/child1", "test", "Child 1" )
        self.assertEquals( len(root.children()), 1 )
        self.assertEquals( child.parent().path, root.path )
        json = loads( root.json(1) )
        self.assertEquals( json["path"], TEST_PATH )
        self.assertEquals( json["kind"], "test" )
        self.assertEquals( json["bunch"], "Test" )
        self.assertEquals( json["children"][0]["bunch"], "Child 1" )       
        json = loads( root.json(0) )
        self.assertFalse( "children" in json )       
        root2 = Bunch.read( root.json() )
        self.assertTrue( root.path == root2.path )
        self.assertTrue( root.kind == root2.kind )
        self.assertTrue( root.bunch == root2.bunch )

    def test_uniq(self):
        one = Bunch.uniq( TEST_PATH )
        two = Bunch.uniq( TEST_PATH, "test" )
        self.assertTrue( one.path != two.path )
        self.assertTrue( one.path != TEST_PATH )
        self.assertTrue( one.kind == GHOST )
        self.assertTrue( two.kind == "test" )

    def test_level(self):
        test = Bunch.resolve( TEST_PATH + "/two" )
        self.assertEquals( test.level(), 3)
        self.assertEquals( Bunch.resolve('/').level(), 0)

    def test_ids(self):
        self.assertEquals( Bunch.resolve('/').xid(), '_' )

    def test_save(self):
        test = Bunch.resolve( TEST_PATH + "/test.txt", "txt", "Test" )
        self.assertEquals( test.fname(), ROOT_DIR + TEST_PATH + '/test.txt' )
        test.bunch = "Test"
        test.save(["redis","file"])

        f = open( test.fname(),"r" )
        self.assertEquals( f.read(), "Test" )
        f.close()

        f = open( test.fname(),"w" )
        f.write("Test2")
        f.close()

        if CACHE: del CACHE[ test.path ]

        test2 = Bunch.resolve( test.path )
        self.assertEquals( test2.bunch, "Test2")

        test.delete(["redis","file"])
        self.assertFalse( os.path.exists( test.fname() ) )
        test2 = Bunch.resolve( test.path, GHOST )
        self.assertEquals( test2.kind, GHOST )
        
    def test_render(self):
	Bunch.resolve( TEMPLATES + "test.template" ).delete(["redis","file"])
        test = Bunch.resolve( TEST_PATH + "/html", "test", "Test" )
        self.assertEquals( test.render(), test.bunch )
	template = Bunch.resolve( TEMPLATES + "test.template" )
        template.bunch = "{{ bunch.kind }}"
        template.save(["redis","file"])
        self.assertEquals( test.render(), test.kind )
        template.delete(["redis","file"])

    def test_ls(self):
        empty = _( TEST_PATH + "/empty", "test", "Content" )
        self.assertEquals( empty.ls(), empty.name() + ": Content" ) 
        _( ROOT_SYS + "templates/menu.template")
        listing = _( ROOT_SYS + "templates").ls(level=2)
        self.assertTrue( "menu.template" in listing  )
        

    def test_execute(self):
        empty = _( TEST_PATH + "/empty" )
        ls = _( "ls %s" % empty.path )
        self.assertEquals( ls.kind, "ls" )
        self.assertEquals( ls.bunch, empty.path )
        res = ls.execute()
        self.assertEquals( res, empty.ls() )

    def test_type(self):
        txt = _( TEST_PATH + "/txt", "test", "<html>\t</html>\r\n" )
        self.assertEquals( txt.mimetype(), "text/html" )
        self.assertFalse( txt.is_binary() )
        bin = _( TEST_PATH + "/bin", "test", "BIN\01\02\03\04" )
        self.assertTrue( bin.is_binary() )

    def test_subscribe(self):

        gotcha = [None,None]

        def handler(who, event):
            gotcha[0] = who
            gotcha[1] = event

        origin = _( TEST_PATH + "/origin" )
        origin.subscribe( handler )
        origin.notify( "Event" )

        self.assertEquals( gotcha[0], origin )
        self.assertEquals( gotcha[1], "Event" )

        origin.unsubscribe( handler )
        origin.notify( "Nope" )
        self.assertEquals( gotcha[1], "Event" )

    def test_parse(self):
        cmd = Bunch.parse( TEST_PATH, GHOST, "cd " + TEST_PATH )
        self.assertEquals( cmd.path, TEST_PATH )
        self.assertEquals( cmd.kind, "cd" )
        self.assertEquals( cmd.bunch, TEST_PATH )
        self.assertEquals( cmd.children()[0].path, TEST_PATH )

    def test_render_cmd(self):
        cmd = _( "render " + TEST_PATH )
        self.assertEquals( cmd.execute(), _( TEST_PATH ).render() )

               
