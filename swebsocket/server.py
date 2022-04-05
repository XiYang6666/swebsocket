import socket
import threading
import time
import queue
from . import coding


def timer(func):
    def inner(*args, **kwargs):
        ftime = time.time()
        r = func(*args, **kwargs)
        print(func.__class__, time.time()-ftime)
        return r
    return inner


class Server:
    def __init__(self, addr: tuple, timeout=30, ping_timer=30, ping_timeout=20,):

        self.network = Server_Network(addr)

        self.is_run = True
        self.Clients = Clients
        self.client_list: list[self.Clients] = []

        self.timeout = timeout
        self.ping_timer = ping_timer
        self.ping_timeout = ping_timeout

        self.network.start()

    def start(self):
        while self.is_run:

            # 处理连接
            try:
                client = self.network.data_queue.get(block=False)
            except:pass
            else:
                self.onconnect(client)

            # 处理用户
            for i in range(len(self.client_list)):
                client = self.client_list[i]
                if client.is_run:
                    #{self.ping_timer}秒ping一次
                    if time.time() - client.last_ping_time >= self.ping_timer:
                        client.ping()
                    #ping后{self.ping_timeout}秒未回应则超时，断开连接
                    if time.time()-client.last_ping_time > self.ping_timeout and client.last_pong_time - client.last_ping_time < 0:
                        client.disconnect(1)

                else:#释放已结束的线程
                    self.client_list[i] = None
            if None in self.client_list:
                self.client_list.remove(None)

    def onconnect(self, client: tuple[socket.socket, tuple]):
        self.client_list.append(self.Clients(*client))


class Server_Network(threading.Thread):
    def __init__(self, addr):
        super().__init__(name="Network")
        self.addr = addr
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(addr)
        self.socket.listen(255)

        self.is_run = True
        self.data_queue = queue.Queue()

    def run(self):
        while self.is_run:
            client = self.socket.accept()
            self.data_queue.put(client)


class Clients(threading.Thread):
    def __init__(self, client: socket.socket, addr, timeout=30):
        super().__init__(name="Client "+str(addr))
        self.socket = client
        self.socket.settimeout(timeout)
        self.addr = addr

        self.is_run = True

        self.last_ping_time = time.time()
        self.last_pong_time = time.time()

        self.start()

    def run(self):
        try:
            recv_data = self.socket.recv(16384).decode()
            recv_message = coding.httpMessage_2_dict(recv_data)
            self.socket.sendall(self.onreceiveRequest(recv_message).encode())
        except:
            self.onhttpMessageError(recv_data)

        while self.is_run:
            try:
                pack = self.socket.recv(16384)
                if pack:
                    data_ = coding.unpack(pack)
                    if data_["MASK"]:
                        data = coding.decode_PayloadData(
                            data_["Payload Data"], data_["Masking-key"])
                        match data_["opcode"]:
                            case 0x1:
                                data = data.decode()
                                self.onmessage(data)
                            case 0x2:
                                data = bytes(data)
                                self.onmessage(data)
                            case 0x8:
                                self.ondisconnect(-2)
                            case 0x9:
                                self.onping()
                            case 0xA:
                                self.onpong(data_)
                    else:
                        self.disconnect(2)
                else:
                    self.ondisconnect(-1)
            except ConnectionAbortedError:
                pass
            except UnicodeDecodeError:
                self.ondataError(pack)
            except:
                pass
    # events 事件

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

        self.send(f"I recv:{message}")

    def onping(self):  # 应该用不上
        """
        收到ping
        """

        self.pong()

    def onpong(self, pack):
        """
        收到pong(ping的回应)
        """
        self.last_pong_time = time.time()

    def ondisconnect(self, code):
        """
        断开连接(对方)

        code:
            -1 : 对方主动断开(TCP)
            -2 : 对方主动断开(websocket)
        """

        self.socket.close()
        self.is_run = False

    # Error event 错误事件
    def onhttpMessageError(self, message: str):
        """
        接收到的报文错误
        """

        print("httpMessageError:\n    ", message)

    def ondataError(self, data: bytes):
        """
        接收收到的数据错误
        """

        print("dataError", data)

    # method 方法

    def send(self, message: str | bytes, **kwarge: any):
        """
        发送消息
        """

        message = message.encode() if type(message) == type(str()) else message
        self.socket.sendall(coding.pack(message, **kwarge))

    def ping(self):
        """
        ping
        """

        self.last_ping_time = time.time()
        self.socket.sendall(coding.pack(opcode=0x9))

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

        self.socket.close()
        self.is_run = False
