"""
Select a JSON library from any of several known libraries.
"""

modules = [('json', 'dumps', 'loads'), 
           ('cjson', 'encode', 'decode'), 
           ('simplejson', 'dumps', 'loads'),
           ('demjson', 'encode', 'decode'),
          ]

while modules:
    module_name, serializer, deserializer = modules.pop(0)
    try:
        json = __import__(module_name)
        encode = getattr(json, serializer)
        decode = getattr(json, deserializer)
        break
    except ImportError:
        if not modules:
            raise ImportError,\
                "could not load one of: json, cjson, simplejson, demjson"

