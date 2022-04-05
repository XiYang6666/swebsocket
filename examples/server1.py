from swebsocket import Server

def onmessage(self,message):
    print(message,self.addr)
    self.send(message)

server=Server(("0.0.0.0",2333))
server.Clients.onmessage=onmessage
print("请打开demo.html")
server.start()