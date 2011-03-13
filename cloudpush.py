from datetime import datetime
from messagequeue import QueueError, MessageQueueManager
from twisted.internet.protocol import Factory, Protocol
from bunch import Bunch, _, GHOST, SEPARATOR
from twisted.web import server, resource
import traceback
import stomper
import os

verbose = False

class BunchProtocol(Protocol):
    id = 0
    def __init__(self):
        self.state = 'initial'
        self.username = None
        self.password = None
        self.buffer = ""
        self.stompBuffer = stomper.stompbuffer.StompBuffer()
        self.lastNull = False
        BunchProtocol.id += 1
        self.id = BunchProtocol.id
        self.avatar = None
        self.receivedDisconnect = False

    def dataReceived(self, data):
        # NOTE: Allow each frame to have an optional '\n'
        # NOTE: binary DOES NOT WORK with this hack in place
        self.stompBuffer.appendData(data.replace('\0', '\0\n'))
        while True:
            msg = self.stompBuffer.getOneMessage()
            # NOTE: the rest of the optional '\n' hack
            if self.stompBuffer.buffer.startswith('\n'):
                self.stompBuffer.buffer = self.stompBuffer.buffer[1:]
            if msg is None:
                break
            if not msg['headers'] and not msg['body'] and not msg['cmd']:
                break
            msg['cmd'] = msg['cmd'].lower()
            getattr(self, 'read_%s' % self.state)(**msg)

    def sendError(self, e):
        exception, instance, tb = traceback.sys.exc_info()
        tbOutput= "".join(traceback.format_tb(tb))
        self.sendFrame('ERROR', {'message': str(e) }, tbOutput)

    def sendFrame(self, cmd, headers, body):
        f = stomper.Frame()
        f.cmd = cmd
        f.headers.update(headers)
        f.body = body 
        self.transport.write(f.pack())

    def autosubscribe(self, subs):
        for sub in subs:
            self.frame_subscribe(({'destination':sub}, None))

    def autounsubscribe(self, unsubs):
        for unsub in unsubs:
            self.frame_unsubscribe(({'destination':unsub}, None))

    def read_initial(self, cmd, headers, body):
        assert cmd == 'connect', "Invalid cmd: expected CONNECT"
        self.username = headers.get('login',"")
        self.password = headers.get('passcode',"")
	self.avatar = Bunch.resolve( SEPARATOR + self.username, "avatar", "Anonymous" )
        self.stomp_connect_succeed()

    def stomp_connect_succeed(self):
        self.state = 'connected'
        self.sendFrame('CONNECTED', {"session": self.id}, "")

    def stomp_connect_failed(self, *args):
        self.sendFrame('ERROR', {'message': "Invalid ID or password"}, "Invalid ID or password")
        self.username = None
        self.transport.loseConnection()

    def read_connected(self, cmd, headers, body):
        getattr(self, 'frame_%s' % cmd)((headers, body))

    def frame_subscribe(self, (headers, body)):
        if "allow" in headers and headers["allow"] == "no":
            return
        try:
            self.factory.mqm.subscribe_queue(self, headers['destination'])
        except QueueError, err:
            self.sendFrame('ERROR',
                           {'message': self.get_message_code(err.code)},
                           self.get_message_text(err.code))

    def frame_unsubscribe(self, (headers, body)):
        self.factory.mqm.leave_queue(self, headers['destination'])

    def frame_send(self, (headers, body)):
        if "allow" in headers and headers["allow"] == "no":
            return
        try:
	    print "EXECUTE: (%s) %s" % ( self.avatar, body )

            body = _( body ).execute()
 
            result = self.factory.mqm.send_message(self, headers['destination'], (headers, body))
        except QueueError, err:
            self.sendFrame('ERROR',
                           {'message': self.get_message_code(err.code)},
                           self.get_message_text(err.code))

    def frame_disconnect(self, (headers, body)):
        self.receivedDisconnect = True
        self.transport.loseConnection()

    def connectionLost(self, reason):
        self.factory.disconnected(self)

    def get_message_code(self, code):
        return {'FAILC': "CREATE error",
                'FAILR': "READ error",
                'FAILW': "WRITE error"}[code]

    def get_message_text(self, code):
        return {'FAILC': "Not authorized to create queue",
                'FAILR': "Not authorized to read queue",
                'FAILW': "Not authorized to write to queue"}[code]

    def send(self, message):
        '''
        This method is invoked by the message queues.
        Not intended for direct use by the protocol.
        '''
        headers, body = message
	print "SEND: ", headers, body
        self.sendFrame('MESSAGE', headers, body )

class BunchFactory(Factory):

    protocol = BunchProtocol

    def __init__(self,verbose=False):
        self.id = 0
        self.verbose = False
        self.mqm = MessageQueueManager()

    def report(self, msg):
        if self.verbose:
            print "[%s] StompFactory: %s" % (datetime.now(), msg)

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
	print "REQUEST:  ", request
        bunch = Bunch.resolve( path, kind[1:] )
	print "RESPONCE: ", bunch
        return str( bunch.render(1) )

