class QueueError(Exception):
    
    def __init__(self, error_code):
        self.code = error_code
        
    def __str__(self):
        return repr(self.code)


class MessageQueueRoot(object):
    def __init__(self, name):
        self.name = name
        self.subscribers = []
        self.id = 0

    def subscribe(self, proto):      
        #print "mqr - subscribe - proto =", proto
        if proto not in self.subscribers:
            self.subscribers.append(proto)
            
    def unsubscribe(self, proto):
        if proto in self.subscribers:
            self.subscribers.remove(proto)
            
    def empty(self):
        return not bool(self.subscribers)


class Queue(MessageQueueRoot):
    """
    A queue sends a message to any one listener
    """
    
    def __init__(self, name):
        MessageQueueRoot.__init__(self, name)
        self.messages = []

    def subscribe(self, proto):
        MessageQueueRoot.subscribe(self, proto)
        while self.messages:
            message = self.messages.pop(0)
            proto.send(message)
            
    def send(self, message):
        """ Calls the send function for each attached protocol """
        if not self.subscribers:
            self.messages.append(message)
        else:
            target = self.subscribers.pop(0)
            target.send(message)
            self.subscribers.append(target)
    
    def empty(self):
        return not bool(self.subscribers or self.messages)
    

class Topic(MessageQueueRoot):
    def send(self, message):
        """ Calls the send function for each attached protocol """
        for proto in self.subscribers:
            proto.send(message)
  

class Pubsub(object):
    """
    Sending to a pubsub queue replicates the message to all subordinate queues. 
    Each pubsub queue contains the list of message queues that should
    receive the message.
    Clients cannot subscribe to the pubsub queue itself, they must subscribe
    to a subordinate queue.
    """
    def __init__(self, name):
        self.baseQueue = Queue(name)
        self.child_queues = []
        
    def add_child(self, queue_ref):
        if queue_ref not in self.child_queues:
            self.child_queues.append(queue_ref)
            
    def remove_child(self, queue_ref):
        if queue_ref in self.child_queues:
            self.child_queues.remove(queue_ref)

    def subscribe(self, proto):
        raise QueueError("FAIL")
            
    def send(self, message):
        """ Calls the send function for each child queue """
        for q in self.child_queues:
            q.send(message)
    
    def empty(self):
        return not bool(len(self.child_queues) > 0)
    

class MessageQueueManager(object):

    def __init__(self):
        self.message_queues = {}
        
    def set_queue_rights(self, queue_rights):
        self.queue_rights = queue_rights

    def test_queue_rights(self, proto, qname, rights):
        if rights not in ('r','w','c'):
            error = "FAIL"+rights.upper()
            raise QueueError(error)
    
    def create_queue(self, proto, dest_name):
        if self.message_queues.has_key(dest_name):
            return
        self.test_queue_rights(proto, dest_name, 'c')
        if dest_name.startswith('/queue/'):
            dest = Queue(dest_name)
        elif dest_name.startswith('/pubsub/'):
            dest = Pubsub(dest_name)
        else: dest = Topic(dest_name)
        self.message_queues[dest_name] = dest
    
    def subscribe_queue(self, proto, dest_name):
        self.create_queue(proto, dest_name)
        self.test_queue_rights(proto, dest_name, 'r')
        self.message_queues[dest_name].subscribe(proto)
    
    def send_message(self, proto, dest_name, message):
        #print "mqm - send - P, D, M", proto, dest_name, message
        self.create_queue(proto, dest_name)
        self.test_queue_rights(proto, dest_name, 'w')
        self.message_queues[dest_name].send(message)
        
    def leave_queue(self, proto, dest_name):
        if self.message_queues.has_key(dest_name):
            self.message_queues[dest_name].unsubscribe(proto)
            
    def destroy_queue(self, proto, dest_name):
        self.create_queue(proto, dest_name)
        self.remove_pubsub_child(self.message_queues[dest_name])
        del self.message_queues[dest_name]
        
    def remove_pubsub_child(self, queue_ref):
        [mq.remove_child(queue_ref) for mq in message_queues 
            if isinstance(mq, Pubsub)]

    def add_pubsub_child(self, proto, dest_name, child_queue):
        self.create_queue(proto, dest_name)
        self.test_queue_rights(proto, child_queue, 'w')
        self.create_queue(proto, child_queue)
        self.message_queues[dest_name].add_child(self.message_queues[child_queue])
    
    def get_list_of_queues(self):
        aRoomList = self.message_queues.keys()
        aRoomList.sort()
        return aRoomList

    def unsubscribe_all_queues(self, proto):
        for q_name in self.message_queues:
            self.message_queues[q_name].unsubscribe(proto)
        
