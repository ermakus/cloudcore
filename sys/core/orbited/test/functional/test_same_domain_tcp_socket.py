from orbited.test.functional import TCPSocketTestCase

class TestSameDomainTCPSocket(TCPSocketTestCase):
    domain = "localhost"
    label = "Same Domain"
