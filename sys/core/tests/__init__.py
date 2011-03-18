import unittest
from test_bunch import BunchTestCase 

def all_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BunchTestCase))
    return suite
