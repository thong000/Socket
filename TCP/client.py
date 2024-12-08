import socket
import os
import time
import multiprocessing
from math import floor


def fileData(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()  # Đọc toàn bộ nội dung tệp
        return content
    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None


def fileDataFrom(file_path, size):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()  # Đọc toàn bộ nội dung tệp
        if size == 0:
            return content[0:]
        else:
            return content[size:]

    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None


def split_string(input_string, delimiter):
    # Sử dụng phương thức split() để chia chuỗi theo ký tự phân cách
    result = input_string.split(delimiter)
    return result


def getFileSize(file_path):
    try:
        file_size = os.path.getsize(file_path)  # Lấy kích thước tệp tính theo byte
        return file_size
    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None


def socketSendNumber(num, soc):
    soc.sendall(str(num).encode())


def socketSendString(string, soc):
    soc.sendall(string.encode('utf-8'))


def socketRecvNumber(soc, size):
    data = soc.recv(size)
    num = int(data.decode())
    return num


def socketRecvString(soc, size):
    data = soc.recv(size)
    return data.decode('utf-8')

def recvByte(soc, size):
    return soc.recv(size)

def writeStringToFile(file_path, content):
    try:
        # Mở tệp ở chế độ ghi ('w'). Nếu tệp đã tồn tại, nó sẽ bị ghi đè.
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(content)  # Ghi chuỗi vào tệp
        print(f"Đã ghi nội dung vào tệp {file_path}")
    except Exception as e:
        print(f"Lỗi khi ghi tệp: {e}")


def isChange(fileName, oldSize):
    curSize = getFileSize(fileName)
    if curSize == None:
        return False
    return curSize != oldSize


HOST = "127.0.0.1"  # IP adress server
PORT = 65432  # port is used by the server

receiver_1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receiver_2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receiver_3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receiver_4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (HOST, PORT)
print("Client connect to server with port: " + str(PORT))
receiver_1.connect(server_address)
receiver_2.connect(server_address)
receiver_3.connect(server_address)
receiver_4.connect(server_address)

def receiveChunk(receiver,connection, chunkSize, part,fileName):
    print(chunkSize)
    if chunkSize < 1024:
        receiver= recvByte(connection,chunkSize)
    else:
        temp = 0
        while temp < chunkSize:
            last = temp + 1024
            if last < chunkSize:
               receiver = receiver + recvByte(connection,1024)
            else:
                receiver=receiver+recvByte(connection,chunkSize%1024)
            temp += 1024
            print(f"[INFO] Downloading {fileName} part {part}: {round(temp/chunkSize*100.0)}%")





def receiveChunk(connection, chunkSize, part,fileName):
    receiver=b""
    print(chunkSize)
    if chunkSize < 1024:
        return recvByte(connection,chunkSize)
    else:
        temp = 0
        while temp < chunkSize:
            last = temp + 1024
            if last < chunkSize:
               receiver = receiver + recvByte(connection,1024)
            else:
                receiver=receiver+recvByte(connection,chunkSize%1024)
            temp += 1024
            print(f"[INFO] Downloading {fileName} part {part}: {floor(temp/chunkSize*100.0)}%")
    return receiver

try:

    size = socketRecvNumber(receiver_1, 1024)
    fileList = socketRecvString(receiver_1, size)
    print("Danh sach cac file co the download la:\n")
    print(fileList)

    start_time = time.time()
    oldSize = getFileSize("Client/input.txt")
    newSize = 0

    while True:
        if isChange("Client/input.txt", oldSize):

            newSize = getFileSize("Client/input.txt")
            changeSize = newSize - oldSize

            split = split_string(fileDataFrom("Client/input.txt", oldSize), '\n')

            for i in range(len(split)):

                if split[i] != "":
                    socketSendNumber(len(split[i]), receiver_1)  # Gui do dai ten file
                    socketSendString(split[i], receiver_1)  # Gui ten file

                    # Nhận kích thước file
                    filesize = int(receiver_1.recv(1024).decode())
                    chunkSize = filesize // 4

                    Des = "Client/" + split[i]

                    """
                    receiver = [b"",b"",b"",b""]  # Noi dung tung chunk
                    
                    
                    receiver1= multiprocessing.Process(target=receiveChunk,
                                                       args=(receiver[0],receiver_1, chunkSize,1,split[i],))
                    receiver2 = multiprocessing.Process(target=receiveChunk,
                                                        args=(receiver[1], receiver_2, chunkSize, 2, split[i],))
                    receiver3 = multiprocessing.Process(target=receiveChunk,
                                                        args=(receiver[2], receiver_3, chunkSize, 3, split[i],))
                    receiver4 = multiprocessing.Process(target=receiveChunk,
                                                        args=(receiver[3], receiver_4, filesize-3*chunkSize, 4, split[i],))

                    processes = [receiver1,receiver2,receiver3,receiver4]

                    receiver1.start()
                    receiver2.start()
                    receiver3.start()
                    receiver4.start()
                    
                    
                    for p in processes:
                        p.join()
                    """

                    receiver=[]
                    receiver.append(receiveChunk(receiver_1, chunkSize,1,split[i]))
                    receiver.append(receiveChunk(receiver_2, chunkSize,2,split[i]))
                    receiver.append(receiveChunk(receiver_3, chunkSize,3,split[i]))
                    receiver.append(receiveChunk(receiver_4, filesize-3*chunkSize,4,split[i]))


                    with open("Client/" + split[i], "wb") as f:
                        f.write(receiver[0])
                        f.write(receiver[1])
                        f.write(receiver[2])
                        f.write(receiver[3])

            oldSize = newSize
        else:
            oldSize = getFileSize("Client/input.txt")
        time.sleep(2)


except KeyboardInterrupt:
    receiver_1.close()
finally:
    receiver_1.close()

