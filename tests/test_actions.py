from bunch import Bunch, GHOST
import unittest

TEST_PATH="/tmp/unit-test"

class ActionsTestCase(unittest.TestCase):
    def setUp(self):
        Bunch.connect( "default" )

    def tearDown(self):
        Bunch.resolve( TEST_PATH ).delete()
        Bunch.disconnect()

    def test_parse(self):
        cmd = Bunch.parse( TEST_PATH, "!cd /tmp")
        self.assertEquals( cmd.path, TEST_PATH )
        self.assertEquals( cmd.kind, "cd" )
        self.assertEquals( cmd.bunch, "/tmp" )
        self.assertEquals( cmd.children()[0].path, "/tmp" )

    def test_ls(self):
        test = Bunch.resolve( TEST_PATH + "/test" )
        Bunch.resolve( TEST_PATH + "/test/1" )
        ls = Bunch.parse( TEST_PATH + "/ls", "!ls " + TEST_PATH + "/test" )
        res = test.execute( ls )
        self.assertEquals( len( res.children() ), 1 )


