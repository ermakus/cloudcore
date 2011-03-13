from orbited.start import _parse_url
from orbited.start import URLParseResult

class TestURLParsing(object):
    fields = ('scheme', 'netloc', 'path', 'params', 'query', 'fragment')
    
    def test_url_parse_result(self):
        test_tuple = (0, 0, 1, 1, 2, 3)
        result = URLParseResult(test_tuple)
        for index, field in enumerate(self.fields):
            assert test_tuple[index] == result[index]
            assert test_tuple[index] == getattr(result, field), field
