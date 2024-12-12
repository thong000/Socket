import socket
import os
import time
from fileinput import filename
from math import floor
from multiprocessing import  Process, Pipe,Lock
from operator import truediv


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

def receiveChunk(pipe, connection, chunkSize, part, fileName,processPipe):

        data=b""
        l=chunkSize//1000

        if chunkSize < l:
            data=data + recvByte(connection, chunkSize)
        else:
            temp=0
            while temp< chunkSize:
                last = temp + l
                if last < chunkSize:
                    data=data+recvByte(connection, l)
                else:
                    data=data+recvByte(connection, chunkSize % l)

                temp = len(data)
                progress=floor(temp/chunkSize*100.0)
                processPipe.send(progress)


        pipe.send(data)





def printProcess(a,b,c,d,pipe1,pipe2,pipe3,pipe4,fileName):


    msg1=0
    msg2=0
    msg3=0
    msg4=0

    while a.is_alive() or b.is_alive() or c.is_alive() or d.is_alive():
        if pipe1.poll():
            msg1 = pipe1.recv()
        if pipe2.poll():
            msg2 = pipe2.recv()
        if pipe3.poll():
            msg3 = pipe3.recv()
        if pipe4.poll():
            msg4 = pipe4.recv()

        # Sử dụng \r để in lại 4 dòng cố định
        print(
            f"\r[INFO] Downloading {fileName} | "
            f"Part 1: {msg1}% | "
            f"Part 2: {msg2}% | "
            f"Part 3: {msg3}% | "
            f"Part 4: {msg4}%    ",end="")


        if msg1>=100 and msg2>=100 and msg3>=100 and msg4>=100:
            break


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
        downloaded=[]


        while True:
            if isChange(folder+"input.txt", oldSize):

                newSize = getFileSize(folder+"input.txt")
                changes = split_string(fileDataFrom(folder+"input.txt", oldSize), '\n')

                for i in range(len(changes)):
                    flag=True
                    if changes[i] in downloaded:
                        flag=False
                        print(f"[INFO] File {changes[i]} da duoc download")
                    if changes[i] != "" and flag :
                        downloaded.append(changes[i])
                        sendNumber(len(changes[i]), receiver[0])  # Gui do dai ten file
                        sendString(changes[i], receiver[0])  # Gui ten file

                        # Nhận kích thước file

                        a=receiver[0].recv(1024).decode()
                        print(a)
                        filesize = int(a)
                        if filesize!=-1:

                            chunkSize = filesize // 4
                            lock = Lock() 
                            output_1, input_1 = Pipe()
                            output_2, input_2 = Pipe()
                            output_3, input_3 = Pipe()
                            output_4, input_4 = Pipe()

                            progress1, p1=Pipe()
                            progress2, p2=Pipe()
                            progress3, p3=Pipe()
                            progress4, p4=Pipe()


                            receiver1 = Process(target=receiveChunk,
                                                               args=(input_1,receiver[0], chunkSize,1,changes[i],p1))
                            receiver2 = Process(target=receiveChunk,
                                                                args=(input_2, receiver[1], chunkSize, 2, changes[i],p2))
                            receiver3 = Process(target=receiveChunk,
                                                                args=(input_3, receiver[2], chunkSize, 3, changes[i],p3))
                            receiver4 = Process(target=receiveChunk,
                                                                args=(input_4, receiver[3], filesize-3*chunkSize, 4, changes[i],p4))
                            processes = [receiver1,receiver2,receiver3,receiver4]



                            for p in processes:
                                p.start()

                            printProcess(receiver1,receiver2,receiver3,receiver4,progress1,progress2,progress3,progress4,changes[i])
                            output=[output_1.recv(),output_2.recv(),output_3.recv(),output_4.recv()]
                            for p in processes:
                                p.join()

                            print(f"\n[DEBUG] Starting to write file {changes[i]}")
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
    start_client("27.27.25.210",65432,"Client/")