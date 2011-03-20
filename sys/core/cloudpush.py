from datetime import datetime
from messagequeue import QueueError, MessageQueueManager
from twisted.internet.protocol import Factory, Protocol
from config import *
from bunch import Bunch, _
from twisted.web import server, resource
import traceback
import stomper
import os

class BunchProtocol(Protocol):
    id = 0
    def __init__(self):
        BunchProtocol.id += 1
        self.id = BunchProtocol.id

    def dataReceived(self, body):
        path = '/'
        self.subscribe( path )
        res = _( body ).execute()
	print "EXEC: %s => %s" % ( body, res )
        if isinstance( res, Bunch ): res = res.render(level=1)
        result = self.factory.mqm.send_message(self, path, res )

    def send(self, body):
        self.transport.write(body)

    def close(self, *args):
        self.transport.loseConnection()

    def subscribe(self, path):
        try:
            self.factory.mqm.subscribe_queue(self, path)
        except QueueError, err:
            raise err

    def unsubscribe(self, path):
        self.factory.mqm.leave_queue(self, path)

class BunchFactory(Factory):

    protocol = BunchProtocol

    def __init__(self,verbose=False):
        self.id = 0
        self.verbose = False
        self.mqm = MessageQueueManager()

    def report(self, msg):
        if self.verbose:
            print "[%s] BunchFactory: %s" % (datetime.now(), msg)

    def disconnected(self, proto):
        self.mqm.unsubscribe_all_queues(proto)

class BunchResource(resource.Resource):

    def getChild(self, path, request):

        if path != "tcp": return BunchResourceLeaf()

        path0 = request.prepath.pop(0)
        request.postpath.insert(0, path0)
        return self


class BunchResourceLeaf(resource.Resource):

    isLeaf = True

    def render_GET(self, request):
        Bunch.connect('default')
	path, kind = os.path.splitext( request.path )
	print " >> ", request
	template = None
        if 'template' in request.args: template = request.args['template'][0]
	level = 1
        if 'level' in request.args: level = int(request.args['level'][0])
       	if path == "" or path == SEPARATOR and template is None:
            bunch = Bunch.resolve( ROOT_SYS + "index.html", "html", "No index file" )
        else:
            bunch = Bunch.resolve( request.path, kind[1:] )
        request.setHeader('Content-Type', bunch.mimetype() )
        if bunch.is_binary(): 
   	    print " << BIN ", bunch
            return bunch.bunch
        res = str( bunch.render(level=level, template=template) )
	print " << TXT ", res
        return res
