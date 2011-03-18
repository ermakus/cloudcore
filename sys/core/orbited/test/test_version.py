import re

import orbited

class TestOrbitedVersioning(object):
    
    def test_orbited_has_a_dunder_version(self):
        assert orbited.__version__
    
    def test_version_is_sensible(self):
        # The versions that we report should always take the form X.Y.Z
        assert re.match(r'\d+(\.\d+(\.\d+))', orbited.__version__)
