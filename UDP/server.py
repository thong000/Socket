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

def ones_complement_checksum(data):
    # Chia dữ liệu thành các khối 16 bit
    if len(data) % 2 != 0:  # Nếu số byte lẻ, thêm 1 byte 0
        data += b'\x00'
    
    checksum = 0
    
    # Duyệt qua từng cặp byte
    for i in range(0, len(data), 2):
        # Kết hợp 2 byte thành một số 16 bit (big-endian)
        word = (data[i] << 8) + data[i + 1]
        checksum += word
        
        # Nếu vượt quá 16 bit, thêm carry vào
        checksum = (checksum & 0xFFFF) + (checksum >> 16)
    
    # Lấy bù 1
    checksum = ~checksum & 0xFFFF
    return checksum

def socketRecvDataWithSeq(server, size, type):
    global ack
    
    max_retries = 10
    retries = 0

    while(retries < max_retries):
        packet, client = server.recvfrom(size + 1024)
        if not packet:
            return None

        #Trong trường hợp các ack ở phần gửi thông tin còn đọng trên buffer
        _ack = packet.split(b"|", 1)
        if len(_ack) != 2:
            continue

        #Trong trường hợp các request ở phần gửi file còn đọng trên buffer
        request = packet.split(b"|", 2)
        if len(request) != 3:
            continue

        seq_number, checksum, data = packet.split(b"|", 2)
        seq = int(seq_number.decode())

        if data == b'FIN':
            ack += 1
            server.sendto(str(ack).encode(), client)
            return data, client

        if(seq == ack + 1 and int(checksum.decode()) == ones_complement_checksum(data)):
            ack += 1
            server.sendto(str(ack).encode(), client)
            if not data:
                return None
            if type == 2:
                return data, client
            if type == 1:  
                return int(data.decode()), client
            else:
                return data.decode(), client
        else:
            server.sendto(str(ack).encode(), client)
            retries += 1
        
def socketSendDataWithSeq(server, client, data):
    global seq

    seq += 1
    if isinstance(data, bytes):  # Nếu dữ liệu là byte
        checksum = ones_complement_checksum(data)
        packet = f"{seq}|{checksum}|".encode() + data
    else:  # Nếu dữ liệu là chuỗi hoặc số
        data = str(data)
        checksum = ones_complement_checksum(data.encode())
        packet = f"{seq}|{checksum}|{data}".encode()

    max_retries = 5
    timeout = 2
    retries = 0

    while(retries < max_retries):
        server.sendto(packet, client)
        server.settimeout(timeout)

        try: 
            while True:
                ack_, _ = server.recvfrom(1024)  # Chờ ACK từ client

                _ack = ack_.split(b"|", 1)
                if len(_ack) == 2: #Nếu file nhận KHÔNG là ack thì bỏ qua. Trong trường hợp file ACK phía trước bị chậm
                    continue

                ack_number = int(ack_.decode())

                if ack_number == seq:
                    #print(f"[INFO] ACK received for seq {seq}")
                    break 
                else:
                    pass
                    #print(f"[ERROR] Wrong ACK")
                    
            if ack_number == seq:
                break
        except socket.timeout:
            retries += 1
            #print(f"[WARN] Timeout waiting for ACK. Retry {retries}/{max_retries}")
        
    server.settimeout(None)

    if retries == max_retries:
        print(f"[ERROR] Failed to send seq {seq}")
        #Nếu không nhận được file ACK sau n lần gửi ta mặc định client đã nhận được. Vì nếu không nhận được hay nhận được rồi thì ta cũng sẽ không tiếp tục gửi.
        return

def sentFile(server, chunk):
    done = 0
    partDone = [1, 1, 1, 1]
    l = 1024

    while True:
        packetReceived, client = server.recvfrom(1024)

        #Trong trường hợp các ack ở phần gửi thông tin còn đọng trên buffer
        _ack = packetReceived.split(b"|", 1)
        if len(_ack) != 2:
            continue

        seq, part_ = packetReceived.split(b"|", 1)

        part = int(part_.decode())

        seq_number = int(seq.decode())
        #print(seq_number)

        chunkSize = len(chunk[part - 1])

        data = b""

        if(seq_number == 0):
            packet = f"{seq_number}|{0}|".encode() + data
            done += partDone[part - 1] #Khi 1 phần được gửi xong, ta sẽ đánh dấu phần đó đã gửi xong
            partDone[part - 1] = 0 #Tránh trường hợp yêu cầu gửi xong của 1 phần bị gửi 2 lần
        else:
            if seq_number * l < chunkSize:
                data = chunk[part - 1][(seq_number - 1) * l : seq_number * l]
            else:
                data = chunk[part - 1][(seq_number - 1) * l :]
            
           
            packet = f"{seq_number}|{ones_complement_checksum(data)}|".encode() + data
        
        server.sendto(packet, client)
        
        if done == 4: #Nếu cả 4 phần đều được gửi xong, ta thoát
            break


seq = 0
ack = 0

def start_server(host, port, file):
    global seq, ack

    # Tao socket chinh va lang nghe client
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((host, port))
    print(f"[INFO] Server listening on {host}:{port}")


    while True:
        seq = 0
        ack = 0
        data, addr = socketRecvDataWithSeq(server, 1024, 0)
        #data, addr = server.recvfrom(1024)
        print(f"[INFO] Received request from {addr}")

        if data.strip() == "GET_FILE":
            # Gui thong tin cua danh sach cac file
            socketSendDataWithSeq(server, addr, getFileSize(file))
            socketSendDataWithSeq(server, addr, fileData(file))

        while True:
            length, _ = socketRecvDataWithSeq(server, 1024, 1)  # Nhan do dai cua ten file
            if length == b'FIN': # Nếu client kết thúc thì out vòng lặp
                print(f"[INFO] Server end with client {addr}")
                break
            fileName, _ = socketRecvDataWithSeq(server, length, 0)
            print(f"[INFO] Received filename from {addr}")

            fileSize = os.path.getsize("Server/" + fileName)
            socketSendDataWithSeq(server, addr, fileSize)

            chunkSize = fileSize//4
            chunk = []

            # Doc file cho tung chunk
            with open("Server/" + fileName, "rb") as f:
                for i in range(3):
                    chunk.append(f.read(chunkSize))
                chunk.append(f.read(fileSize-3*chunkSize))

            sentFile(server, chunk)



if __name__ == "__main__":
    start_server("127.0.0.1", 65432,"Server/fileList.txt")