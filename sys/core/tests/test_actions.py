from bunch import Bunch, _, GHOST
import unittest

TEST_PATH="/tmp/unit-test"
TEST_DB=0

class ActionsTestCase(unittest.TestCase):
    def setUp(self):
        Bunch.connect( TEST_DB )

    def tearDown(self):
        Bunch.resolve( TEST_PATH ).delete()
        Bunch.disconnect()

    def test_parse(self):
        cmd = Bunch.parse( TEST_PATH, GHOST, "cd /tmp")
        self.assertEquals( cmd.path, TEST_PATH )
        self.assertEquals( cmd.kind, "cd" )
        self.assertEquals( cmd.bunch, "/tmp" )
        self.assertEquals( cmd.children()[0].path, "/tmp" )

    def test_render(self):
        cmd = _( "render " + TEST_PATH )
        self.assertEquals( cmd.execute(), _( TEST_PATH ).render() )
        
