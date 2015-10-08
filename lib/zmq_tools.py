# from __future__ import print_function, unicode_literals

import zmq




def send_message(message, hostname='localhost', port=5556):
    with zmq.Context() as ctx:
        with ctx.socket(zmq.REQ) as sock:
            sock.connect('tcp://%s:%d' % (hostname, port))
            req = unicode(message)
            sock.send_string(req)
            # import ipdb; ipdb.set_trace()# rep = sock.recv_string()
            import ipdb; ipdb.set_trace()

if __name__=="__main__":
    send_message('test')
                
