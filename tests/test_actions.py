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
        cmd = Bunch.parse( TEST_PATH, GHOST, "cd /tmp")
        self.assertEquals( cmd.path, TEST_PATH )
        self.assertEquals( cmd.kind, "cd" )
        self.assertEquals( cmd.bunch, "/tmp" )
        self.assertEquals( cmd.children()[0].path, "/tmp" )

