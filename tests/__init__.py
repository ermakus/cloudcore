import unittest
from test_bunch import BunchTestCase 
from test_actions import ActionsTestCase 

def all_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BunchTestCase))
    suite.addTest(unittest.makeSuite(ActionsTestCase))
    return suite
