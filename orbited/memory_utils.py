
class MemoryUtil(object):
    
    @staticmethod
    def instance_counts(instances):
        totals = {}
        for instance in instances:
            klassname = instance.__class__.__name__
            if klassname not in totals:
                totals[klassname] = 0
            totals[klassname] += 1
        return sorted(totals.items(), key=lambda (klassname, count): -count)
    
    @classmethod
    def add_options_to_parser(cls, parser):
        parser.add_option(
            "-m",
            "--manhole",
            dest="manhole_port",
            action="store",
            default=None,
            help="start a twisted.manhole telnet server on this port"
            )
        parser.add_option(
            "--manhole-password",
            dest="manhole_password",
            action="store",
            default="secret",
            help="use the argument as the password for the manhole server account 'admin'"
            )
    
    @classmethod
    def manhole_requested(self, options):
        return bool(options.manhole_port)
    
    def __init__(self, options):
        self.port = int(options.manhole_port)
        self.password = options.manhole_password
    
    def install(self, reactor):
        import objgraph
        from twisted.manhole import telnet
        def createShellServer():
            manhole_port = self.port
            factory = telnet.ShellFactory()
            port = reactor.listenTCP(manhole_port, factory)
            factory.username = 'admin'
            factory.password = self.password
            factory.namespace['objgraph'] = objgraph
            factory.namespace['memory_util'] = self
            print "Manhole listening on port %s", manhole_port
            return port
        reactor.callWhenRunning(createShellServer)
