import socket
import os
import time

def fileData(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()  # Đọc toàn bộ nội dung tệp
        return content
    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None

def getFileSize(file_path):
    try:
        file_size = os.path.getsize(file_path)  # Lấy kích thước tệp tính theo byte
        return file_size
    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None

def socketSendDataWithSeq(server, client, data):
    global seq
    
    if isinstance(data, bytes):  # Nếu dữ liệu là byte
        packet = f"{seq}|".encode() + data
    else:  # Nếu dữ liệu là chuỗi hoặc số
        packet = f"{seq}|{data}".encode()

    max_retries = 5
    timeout = 2
    retries = 0

    while(retries < max_retries):
        server.sendto(packet, client)
        #server.settimeout(timeout)

        try: 
            ack, _ = server.recvfrom(1024)  # Chờ ACK từ client
            ack_number = int(ack.decode())

            if ack_number == seq:
                print(f"[INFO] ACK received for seq {seq}")
                seq += 1
                break 
        except socket.timeout:
            retries += 1
        
    if retries == max_retries:
        print(f"[ERROR] Failed to send seq {seq}")
        return

def socketRecvNumber(server, size):
    data, _ = server.recvfrom(size)
    num = int(data.decode())
    return num

def socketRecvString(server, size):
    data, _ = server.recvfrom(size)
    return data.decode()

def socketRecvDataWithSeq(server, client, size, type):
    global ack

    max_retries = 5
    retries = 0

    while(retries < max_retries):
        packet, _ = server.recvfrom(size + 100)
        if not packet:
            return None
        seq_number, data = packet.split(b"|", 1)
        seq = int(seq_number.decode())

        if(seq == ack):
            server.sendto(str(ack).encode(), client)
            ack += 1
            if type == 1:  
                return int(data.decode())
            else:
                return data.decode()
        else:
            server.sendto(str(ack - 1).encode(), client)
            retries += 1
        
seq = 0
ack = 0

def start_server(host, port, file):
    global seq

    # Tao socket chinh va lang nghe client
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((host, port))
    print(f"[INFO] Server listening on {host}:{port}")


    while True:
        data, addr = server.recvfrom(1024)
        print(f"[INFO] Received request from {addr}")

        if data.decode().strip() == "GET_FILE":
            # Gui thong tin cua danh sach cac file
            socketSendDataWithSeq(server, addr, getFileSize(file))
            socketSendDataWithSeq(server, addr, fileData(file))

        while True:
            length = socketRecvDataWithSeq(server, addr, 1024, 1)  # Nhan do dai cua ten file
            fileName = socketRecvDataWithSeq(server, addr, length, 2)
            print(f"[INFO] Received filename from {addr}")

            fileSize = os.path.getsize("Server/" + fileName)
            socketSendDataWithSeq(server, addr, fileSize)

            with open("Server/" + fileName, "rb") as f:
                while data := f.read(1024):
                    socketSendDataWithSeq(server, addr, data)




if __name__ == "__main__":
    start_server("127.0.0.1", 65432,"Server/fileList.txt")