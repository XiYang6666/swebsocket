from re import S
import swebsocket

class Server(swebsocket.Server):
    def __init__(self,addr):
        super().__init__(addr)
        self.Clients=Clients

class Clients(swebsocket.Clients):
    def __init__(self,*arge):
        super().__init__(*arge)

    def onmessage(self, message: str | bytes):
        print(self.addr,message)
        self.send(message)

s=Server(("",2333))
print("请打开demo.html")
s.start()