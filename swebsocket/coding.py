import struct
import re
import random
import base64
import hashlib
import os


def httpMessage_2_dict(http_message) -> dict :
    header_dict={}
    temp=http_message.split("\r\n\r\n")
    temp[0]=temp[0].split("\r\n")

    header_dict["method"]      = temp[0][0].split(" ",3)
    header_dict["headers"]     = dict([re.split(r": ?",i,maxsplit=1)for i in temp[0][1:]])
    if temp[1] != "":
        header_dict["entity-body"] = temp[1]

    return header_dict

def dict_2_httpMessage(header_dict:dict) -> str :
    http_message=""

    http_message+=f'{" ".join(header_dict["method"])}\r\n'
    http_message+="".join([f'{i}: {header_dict["headers"][i]}\r\n' for i in header_dict["headers"]])
    http_message+="\r\n"
    if "entity-body" in header_dict:
        http_message+=header_dict["entity-body"]

    return http_message


def create_accept(data):
    return base64.b64encode(hashlib.sha1((data+"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode('utf-8')).digest()).decode()

def unpack(payload) -> dict:
    FIN         = bool ((struct.unpack(">H",payload[0:2])[0] & 0b1000_0000_0000_0000 ) >> 15 )
    RSV1        = bool ((struct.unpack(">H",payload[0:2])[0] & 0b0100_0000_0000_0000 ) >> 14 )
    RSV2        = bool ((struct.unpack(">H",payload[0:2])[0] & 0b0010_0000_0000_0000 ) >> 13 )
    RSV3        = bool ((struct.unpack(">H",payload[0:2])[0] & 0b0001_0000_0000_0000 ) >> 12 )
    opcode      = int  ((struct.unpack(">H",payload[0:2])[0] & 0b0000_1111_0000_0000 ) >> 8  )
    MASK        = bool ((struct.unpack(">H",payload[0:2])[0] & 0b0000_0000_1000_0000 ) >> 7  )
    Payload_len = int  ((struct.unpack(">H",payload[0:2])[0] & 0b0000_0000_0111_1111 ) >> 0  )

    match Payload_len:
        case 126:
            Extended_payload_length = struct.unpack(">H",payload[2:4])[0]
            data_length          = Extended_payload_length
            Masking_key             = payload[4:8]
            decoded_start           = 8
        case 127:
            Extended_payload_length = struct.unpack(">L",payload[2:10])[0]
            data_length          = Extended_payload_length
            Masking_key             = payload[10:14]
            decoded_start           = 14
        case _ :
            Extended_payload_length = 0
            data_length          = Payload_len
            Masking_key             = payload[2:6]
            decoded_start           = 6

    Payload_Data = payload[decoded_start:decoded_start+data_length]

    return {
        "FIN"                     : FIN,
        "RSV1"                    : RSV1,
        "RSV2"                    : RSV2,
        "RSV3"                    : RSV3,
        "opcode"                  : opcode,
        "MASK"                    : MASK,
        "Payload len"             : Payload_len,
        "Extended payload length" : Extended_payload_length,
        "Masking-key"             : Masking_key,
        "Payload Data"            : Payload_Data,
      # "Data length"             : data_length,
    }

def pack(Payload_Data=b"",**kwarge:dict) -> bytes:
    FIN          :bool  = kwarge.get("FIN")          if "FIN"          in kwarge else True
    RSV1         :bool  = kwarge.get("RSV1")         if "RSV1"         in kwarge else False
    RSV2         :bool  = kwarge.get("RSV2")         if "RSV2"         in kwarge else False
    RSV3         :bool  = kwarge.get("RSV3")         if "RSV3"         in kwarge else False
    opcode       :int   = kwarge.get("opcode")       if "opcode"       in kwarge else 1
    MASK         :bool  = kwarge.get("MASK")         if "MASK"         in kwarge else False
    Masking_key  :bytes = kwarge.get("Masking-key")  if "Masking-Key"  in kwarge else b""
    Payload_Data :bytes = kwarge.get("Payload_Data") if "Payload_Data" in kwarge else Payload_Data

    #
    # if MASK:
    #     Payload_Data,Masking_key=encode_PayloadData(Payload_Data)
    # else:
    #     Masking_key=b""
    #

    Payload_Data,Masking_key = encode_PayloadData(Payload_Data,Masking_key,True) if MASK else Payload_Data,Masking_key

    length =  len(Payload_Data)
    if length <= 125:
        Payload_len = length
        Extended_payload_length = b""
    elif length <= 0xff_ff:
        Payload_len = 126
        Extended_payload_length = struct.pack(">h",length)
    elif length <= 0xff_ff_ff_ff_ff_ff_ff_ff:
        Payload_len = 127
        Extended_payload_length = struct.pack(">q",length)

    pack_data=struct.pack(
        ">H",
        FIN         <<15 |  \
        RSV1        <<14 |  \
        RSV2        <<13 |  \
        RSV3        <<12 |  \
        opcode      <<8  |  \
        MASK        <<7  |  \
        Payload_len
    )+\
    Extended_payload_length +\
    Masking_key             +\
    Payload_Data
        
    
    return pack_data


def decode_PayloadData(Payload_Data:bytes,Masking_key=None) -> bytes:
    
    if Masking_key is None :
        # MASK=False
        #bytes_list=bytearray(Payload_Data)
        pass
    else:
        # MASK=True
        bytes_list = bytearray()
        for i in range(len(Payload_Data)):
            chunk = Payload_Data[i] ^ Masking_key[i % 4]
            bytes_list.append(chunk)
        Payload_Data=bytes(bytes_list)

    #
    # if MASK:
    #     bytes_list = bytearray()
    #     for i in range(len(Payload_Data)):
    #         chunk = Payload_Data[i] ^ Masking_key[i % 4]
    #         bytes_list.append(chunk)
    # else: bytes_list=bytearray(Payload_Data)
    #
    
    #data=bytes(bytes_list)

    return Payload_Data



def encode_PayloadData(Payload_data,Masking_key=None,MASK=False):
    if MASK:
        Masking_key = os.urandom(4) if Masking_key is None else Masking_key

        bytes_list = bytearray()
        for i in range(len(Payload_Data)):
            chunk = Payload_Data[i] ^ Masking_key[i % 4]
            bytes_list.append(chunk)
        Payload_Data=bytes(bytes_list)

    else:
        pass

    return Payload_data,Masking_key
    



#if __name__ == "__main__":
    #print(encode_PayloadData(b"ddsdds",MASK=True))
