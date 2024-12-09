import socket
import os
import time
from math import floor
from multiprocessing import  Process, Pipe



def fileDataFrom(file_path, size):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        if size == 0:
            return content[0:]
        else:
            return content[size:]

    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None


def split_string(input_string, delimiter):
    result = input_string.split(delimiter)
    return result


def getFileSize(file_path):
    try:
        file_size = os.path.getsize(file_path)  # Lấy kích thước tệp tính theo byte
        return file_size
    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return -1



def sendNumber(num, soc):
    soc.sendall(str(num).encode())

def sendString(string, soc):
    soc.sendall(string.encode('utf-8'))

def recvNumber(soc, size):
    return int(soc.recv(size).decode())

def recvString(soc, size):
    return soc.recv(size).decode('utf-8')

def recvByte(soc, size):
    return soc.recv(size)

def isChange(fileName, oldSize):
    curSize = getFileSize(fileName)
    if curSize == None:
        return False
    return curSize != oldSize

def receiveChunk(pipe, connection, chunkSize, part, fileName):

        data=b""
        if chunkSize < 1024:
            data=data + recvByte(connection, chunkSize)
        else:
            temp = 0
            while temp < chunkSize:
                last = temp + 1024
                if last < chunkSize:
                    data=data+recvByte(connection, 1024)
                else:
                    data=data+recvByte(connection, chunkSize % 1024)

                temp += 1024
                print(f"[INFO] Downloading {fileName} part {part}: {floor(temp/chunkSize*100.0)}%")

        pipe.send(data)








def start_client(serverIP,serverPort,folder):

    receiver = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(4)]

    server_address = (serverIP, serverPort)
    print("[INFO]Client connect to server with port: " + str(serverPort))

    for clientSocket in receiver:
        clientSocket.connect(server_address)

    try:

        size = recvNumber(receiver[0], 1024)
        fileList = recvString(receiver[0], size)
        print(f"[INFO]Danh sach cac file co the download la:\n{fileList}\n")

        start_time = time.time()
        oldSize = getFileSize(folder+"input.txt")


        while True:
            if isChange(folder+"input.txt", oldSize):

                newSize = getFileSize(folder+"input.txt")
                changes = split_string(fileDataFrom(folder+"input.txt", oldSize), '\n')

                for i in range(len(changes)):

                    if changes[i] != "":
                        sendNumber(len(changes[i]), receiver[0])  # Gui do dai ten file
                        sendString(changes[i], receiver[0])  # Gui ten file

                        # Nhận kích thước file
                        filesize = int(receiver[0].recv(1024).decode())
                        if filesize!=-1:

                            chunkSize = filesize // 4

                            output_1, input_1 = Pipe()
                            output_2, input_2 = Pipe()
                            output_3, input_3 = Pipe()
                            output_4, input_4 = Pipe()


                            receiver1 = Process(target=receiveChunk,
                                                               args=(input_1,receiver[0], chunkSize,1,changes[i]))
                            receiver2 = Process(target=receiveChunk,
                                                                args=(input_2, receiver[1], chunkSize, 2, changes[i]))
                            receiver3 = Process(target=receiveChunk,
                                                                args=(input_3, receiver[2], chunkSize, 3, changes[i]))
                            receiver4 = Process(target=receiveChunk,
                                                                args=(input_4, receiver[3], filesize-3*chunkSize, 4, changes[i]))
                            processes = [receiver1,receiver2,receiver3,receiver4]



                            for p in processes:
                                p.start()

                            output=[output_1.recv(),output_2.recv(),output_3.recv(),output_4.recv()]


                            for p in processes:
                                p.join()

                            print(f"[DEBUG] Starting to write file {changes[i]}")
                            with open(folder+changes[i], "wb") as f:
                                for data in output:
                                    f.write(data)
                                print(f"[INFO] Da ghi file {changes[i]}")
                        else:
                            print(f"[INFO] File {changes[i]} khong ton tai tren server")
                oldSize = newSize
            else:
                oldSize = getFileSize(folder+"input.txt")
            time.sleep(5)


    except KeyboardInterrupt:
        sendNumber(-2,receiver[0])
        time.sleep(3)
        print("[INFO] Da ket thuc chuong trinh")
        for clientSocket in receiver:
            clientSocket.close()
    finally:
        for clientSocket in receiver:
            clientSocket.close()

if __name__ == "__main__":
    start_client("127.0.0.1",65432,"Client/")