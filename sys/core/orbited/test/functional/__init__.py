import os
import re
import signal
import sys
import time

from orbited.test.resources.selenium import selenium

class TCPSocketTestCase(object):
    
    def test_tcp_socket(self):
        BROWSERS = ["*firefox",
                    ]
        
        for browser in BROWSERS:
            sel = selenium('localhost', 4444, browser, "http://%s:8000/" % self.domain)
            sel.start()
            yield self._tcp_socket_test, sel, browser
            sel.stop()
    
    def _tcp_socket_test(self, sel, browser):
        sel.open("/static/tests/")
        sel.click("link=%s" % self.label)
        sel.wait_for_page_to_load("30000")
        time.sleep(1)
        assert sel.is_text_present("TEST SUMMARY")
        time.sleep(1)
        assert sel.is_text_present("5 tests in 1 groups")
        assert sel.is_text_present("0 errors")
        assert sel.is_text_present("0 failures")
