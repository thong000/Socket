import socket
import os
import time
from math import floor
from multiprocessing import  Process, Pipe




### Cac ham thao tác voi file
def getFileData(filePath):
    try:
        with open(filePath, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"[INFO] Tep {filePath} khong ton tai")
        return None

def splitString(string, delimiter):
    result = string.split(delimiter)
    while "" in result:
        result.remove("")
    return result

def getFileSize(filePath):
    try:
        fileSize = os.path.getsize(filePath)
        return fileSize
    except FileNotFoundError:
        print(f"[INFO] Tep {filePath} khong ton tai")
        return -1
    
def countChangedCharacters(fileName, oldSize):
    try:
        curSize = getFileSize(fileName)
        if curSize == -1:
            return 0
        sizeChange=curSize-oldSize
        oldSize=curSize
        return sizeChange
    except FileNotFoundError:
        return 0




### Cac ham gui va nhan 
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



def receiveChunk(dataPipe, connection, chunkSize, progressPipe):

        data=b""
        bytePerRecv=chunkSize//1000

        temp=0
        while temp < chunkSize:
            last = temp + bytePerRecv
            if last < chunkSize:
                data=data+recvByte(connection, bytePerRecv)
            else:
                data=data+recvByte(connection, chunkSize % bytePerRecv)

            temp = len(data)
            progressPipe.send(floor(temp/chunkSize*100.0))


        dataPipe.send(data)



def printProgress(pipe_1, pipe_2, pipe_3, pipe_4, fileName):

    msg_1 = msg_2 = msg_3 = msg_4 = 0

    while True:
        if pipe_1.poll(): msg_1 = pipe_1.recv()
        if pipe_2.poll(): msg_2 = pipe_2.recv()
        if pipe_3.poll(): msg_3 = pipe_3.recv()
        if pipe_4.poll(): msg_4 = pipe_4.recv()

        print(f"\r[INFO] Downloading {fileName} | "
            f"Part 1: {msg_1}% | "
            f"Part 2: {msg_2}% | "
            f"Part 3: {msg_3}% | "
            f"Part 4: {msg_4}%   ",end="")

        if msg_1>=100 and msg_2>=100 and msg_3>=100 and msg_4>=100:
            break


def start_client(serverIP,serverPort,folder):

    # Tao 4 socket va connect toi server
    receiver = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(4)]

    server_address = (serverIP, serverPort)
    print("[INFO] Client connect to server: "+str(server_address))

    for clientSocket in receiver:
        clientSocket.connect(server_address)

    try:

        fileListSize = recvNumber(receiver[0], 1024)
        fileList = recvString(receiver[0], fileListSize)
        print(f"[INFO] Danh sach cac file co the download la:\n{fileList}\n")


        oldSize = getFileSize(folder+"input.txt")
        downloaded=[]
        isDownloaded = True


        while True:

            sizeChanged=countChangedCharacters(folder + "input.txt", oldSize)

            if sizeChanged>0:

                fileData=getFileData(folder+"input.txt")
                fileNames = splitString(fileData[-sizeChanged:], '\n')

                for i in range(len(fileNames)):

                    if fileNames[i] in downloaded:
                        isDownloaded=False
                        print(f"[INFO] File {fileNames[i]} da duoc download")


                    if  isDownloaded :
                        downloaded.append(fileNames[i])
                        sendNumber(len(fileNames[i]), receiver[0])
                        sendString(fileNames[i], receiver[0])

                        # Nhận kích thước file
                        fileSize = recvNumber(receiver[0],1024)

                        if fileSize!=-1:  # Truong hop file khong co tren server

                            chunkSize = fileSize // 4

                            # Tao cac Pipe de giao tiep giua cac process
                            pipes = [Pipe() for _ in range(8)]
                            outputs, inputs = zip(*pipes)
                            output_1, output_2, output_3, output_4,progress_1, progress_2,progress_3, progress_4= outputs
                            input_1, input_2, input_3, input_4, p1, p2, p3, p4 = inputs


                            # Tao cac ham nhan song song
                            receiver1 = Process(target=receiveChunk,
                                                               args=(input_1,receiver[0], chunkSize,p1))
                            receiver2 = Process(target=receiveChunk,
                                                                args=(input_2, receiver[1], chunkSize,p2))
                            receiver3 = Process(target=receiveChunk,
                                                                args=(input_3, receiver[2], chunkSize,p3))
                            receiver4 = Process(target=receiveChunk,
                                                                args=(input_4, receiver[3], fileSize-3*chunkSize,p4))

                            processes = [receiver1,receiver2,receiver3,receiver4]

                            for p in processes:
                                p.start()

                            printProgress(progress_1, progress_2, progress_3, progress_4, fileNames[i]) # In phan tram
                            output=[output_1.recv(),output_2.recv(),output_3.recv(),output_4.recv()] # Data nhan duoc

                            for p in processes:
                                p.join()

                            print(f"\n[DEBUG] Starting to write file {fileNames[i]}")
                            with open(folder+fileNames[i], "wb") as f:
                                for data in output:
                                    f.write(data)
                                print(f"[INFO] Da ghi file {fileNames[i]}")

                        else:
                            print(f"[INFO] File {fileNames[i]} khong ton tai tren server")

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