import socket
import os
import time

def getFileSize(file_path):
    try:
        file_size = os.path.getsize(file_path)  # Lấy kích thước tệp tính theo byte
        return file_size
    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None

def fileDataFrom(file_path, size):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()  # Đọc toàn bộ nội dung tệp
        if size==0:
            return content[0:]
        else:
            return content[size:]

    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None

def fileData(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()  # Đọc toàn bộ nội dung tệp
        return content
    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None

def isChange(fileName,oldSize):
    curSize = getFileSize(fileName)
    if curSize == None:
        return False
    return curSize != oldSize

def socketRecvDataWithSeq(client, server_address, size, type):
    global ack

    max_retries = 10
    retries = 0

    while(retries < max_retries):
        packet, _ = client.recvfrom(size + 1024)
        if not packet:
            return None

        _ack = packet.split(b"|", 1)
        if len(_ack) != 2: #Nếu file nhận là ack thì bỏ qua. Trong trường hợp lệnh sent phía trước bị dư
            continue

        seq_number, data = packet.split(b"|", 1)
        seq = int(seq_number.decode())

        if(seq == ack + len(data)):
            ack += len(data)
            client.sendto(str(ack).encode(), server_address)
            if not data:
                return None
            if type == 2:
                return data
            if type == 1:  
                return int(data.decode())
            else:
                return data.decode()
        else:
            print(f"[INFO] ERROR seq number")
            client.sendto(str(ack).encode(), server_address)
            retries += 1
        
def socketSendDataWithSeq(client, server, data):
    global seq
    
    #Nếu không nhận được file ACK sau n lần gửi ta mặc định client đã nhận được. Vì nếu không nhận được hay nhận được rồi thì ta cũng sẽ không tiếp tục gửi.
    
    if isinstance(data, bytes):  # Nếu dữ liệu là byte
        seq += len(data)
        packet = f"{seq}|".encode() + data
    else:  # Nếu dữ liệu là chuỗi hoặc số
        data = str(data)
        seq += len(data.encode())
        packet = f"{seq}|{data}".encode()

    max_retries = 5
    timeout = 2
    retries = 0

    while(retries < max_retries):
        client.sendto(packet, server)
        client.settimeout(timeout)

        try: 
            while True:
                ack_, _ = client.recvfrom(1024)  # Chờ ACK từ server

                _ack = ack_.split(b"|", 1)
                if len(_ack) == 2: #Nếu file nhận KHÔNG là ack thì bỏ qua. Trong trường hợp file ACK phía trước bị chậm phía trước bị dư
                    continue

                ack_number = int(ack_.decode())

                if ack_number == seq:
                    print(f"[INFO] ACK received for seq {seq}")
                    break 
                else:
                    print(f"[ERROR] Wrong ACK")
            
            if ack_number == seq:
                break
        except socket.timeout:
            retries += 1
    
    client.settimeout(None)

    if retries == max_retries:
        print(f"[ERROR] Failed to send seq {seq}")
        return

def socketSendNumber(num, server, client):
    server.sendto(str(num).encode(), client)

def socketSendString(string, server, client):
    server.sendto(string.encode(), client)

def split_string(input_string, delimiter):
    # Sử dụng phương thức split() để chia chuỗi theo ký tự phân cách
    result = input_string.strip().split(delimiter)
    return result

def get_num(key, fileList):
    for i in range(len(fileList)):
        if key == fileList[i]:
            return i 
    return -1

HOST = "127.0.0.1"  # IP adress server
PORT = 65432        # port is used by the server

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = (HOST, PORT)
seq = 0
ack = 0

socketSendDataWithSeq(client, server_address, "GET_FILE")
#client.sendto(b"GET_FILE", server_address)

try:

        size = socketRecvDataWithSeq(client, server_address, 1024, 1)
        #print(size)
        data = socketRecvDataWithSeq(client, server_address, size, 0)
        print("Danh sach cac file co the download la:")
        fileList = split_string(data, '\n')
        fileSent = []
        for i in range(len(fileList)):
            fileSent.append(0)
            print(fileList[i], fileSent[i], sep = ' ')

        start_time = time.time()
        oldSize = getFileSize("Client/input.txt")
        newSize = 0

        while True:
            if isChange("Client/input.txt", oldSize):

                newSize = getFileSize("Client/input.txt")
                changeSize = newSize - oldSize

                split = split_string(fileData("Client/input.txt"), '\n')
                #print(len(split))

                for i in range(len(split)):
                    if split[i] != "":

                        k = get_num(split[i], fileList)

                        if k == -1:
                            print("Khong ton tai file, vui long kiem tra ten file!")
                            break

                        if fileSent[k] == 1:
                            continue

                        fileSent[k] = 1

                        socketSendDataWithSeq(client, server_address, len(split[i]))
                        socketSendDataWithSeq(client, server_address, split[i])

                        #client1.sendall(b"ACK")  # Gửi phản hồi
                        filesize = socketRecvDataWithSeq(client, server_address, 1024, 1)

                        Des = "Client/"+split[i]

                        length = 0
                        

                        with open("Client/" + split[i],"wb") as f:
                            while(length < filesize):
                                receiver = socketRecvDataWithSeq(client, server_address, 1024, 2)
                                if not receiver:
                                    break
                                length += len(receiver)
                                print(f"\r[INFO] Downloading {split[i]}: {round((length / filesize) * 100)}%", end = "")
                                f.write(receiver)
                        
                        print("\n")



                oldSize = newSize
            else:
                oldSize = getFileSize("Client/input.txt")
            time.sleep(2)

except KeyboardInterrupt:
    client.close()
finally:
    client.close()
