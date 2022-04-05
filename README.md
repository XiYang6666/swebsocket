# swebsocket
 A python websocket server
 一个websocket 服务端库

create a server
```python
import swebsocket

class Server(swebsocket.Server):
    def __init__(self,addr):
        super().__init__(addr)
        self.Clients=Clients

class Clients(swebsocket.Clients):
    def __init__(self,*arge):
        super().__init__(*arge)

    
    def onreceiveRequest(self, request_message):
        """
        收到连接报文

        此函数应返回回应的报文
        """

        send_message = {
            "method": [
                "HTTP/1.1",
                "101",
                "Switching Protocols",
            ],
            "headers": {
                "Upgrade": "websocket",
                "Connection": "Upgrade",
                "Sec-WebSocket-Accept": coding.create_accept(request_message["headers"]["Sec-WebSocket-Key"]),
                "WebSocket-Location": request_message["headers"]["Host"],
            },
        }
        return coding.dict_2_httpMessage(send_message)

    def onmessage(self, message: str | bytes):
        """
        接收到消息
        """

        """
        self.send(f"I recv:{message}")
        ......
        """

    def onping(self):  # 应该用不上
        """
        收到ping
        """

        self.pong()

    def onpong(self, pack):
        """
        收到pong(ping的回应)
        """
        """
        self.last_pong_time = time.time()
        ......
        """

    def ondisconnect(self, code):
        """
        断开连接(对方)

        code:
            -1 : 对方主动断开(TCP)
            -2 : 对方主动断开(websocket)
        """

        """
        self.socket.close()
        self.is_run = False
        ......
        """

    # 错误事件
    def onhttpMessageError(self, message: str):
        """
        接收到的报文错误
        """
        """
        print("httpMessageError:\n    ", message)
        ......
        """

    def ondataError(self, data: bytes):
        """
        接收收到的数据错误
        """
        """
        print("dataError", data)
        ......
        """

    # 方法

    def send(self, message: str | bytes, **kwarge: any):
        """
        发送消息
        """

        """
        message = message.encode() if type(message) == type(str()) else message
        self.socket.sendall(coding.pack(message, **kwarge))
        ......
        """

    def ping(self):
        """
        ping
        """

        """
        self.last_ping_time = time.time()
        self.socket.sendall(coding.pack(opcode=0x9))
        ......
        """

    def pong(self):  # 应该也用不上
        """
        pong(回应ping)
        """

        pass

    def disconnect(self, code=0):
        """
        断开连接(自己主动断开)

        code:
            0:主动断开
            1:超时
            2:错误
        """
     

s=Server(("",2333))
print("请打开demo.html")
s.start()
```
