import socket
import os
import multiprocessing


def getFileData(filePath):
    try:
        with open(filePath, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"[INFO] Tệp {filePath} khong ton tai.")
        return None

def getFileSize(filePath):
    try:
        fileSize = os.path.getsize(filePath)
        return fileSize
    except FileNotFoundError:
        print(f"[INFO] Tệp {filePath} khong ton tai.")
        return -1

# Cac ham gui va nhan
# Note: do ham sendall chi gui duoc du lieu byte nen neu muon gui
# du lieu loai khac thi phai encode, khi nhan thi dung decode

def sendNumber(num, soc):
    soc.sendall(str(num).encode())
def sendString(string, soc):
    soc.sendall(string.encode('utf-8'))
def sendByte(byte, soc):
    soc.sendall(byte)
def recvNumber(soc, size):
        return int(soc.recv(size).decode())
def recvString(soc, size):
        return soc.recv(size).decode()


def sendChunk(connection, chunk,fileName,address):
    print(f"[INFO] Dang gui mot chunk cua file  {fileName} den {address}")

    length=len(chunk)
    bytePerSend=length//1000

    temp=0
    while temp<length:
        first=temp
        last=temp+bytePerSend
        if last<length:
            sendByte(chunk[first:last],connection)
        else:
            sendByte(chunk[first:], connection)
        temp+=bytePerSend
    print(f"[INFO] Da gui file mot chunk cua file {fileName} den {address}")



def handleClient(socketList, folder, clientAddress):
    while True:
            fileNameLength=recvNumber(socketList[0], 1024) # Nhan do dai cua ten file can tai

            # Khi client nhan tin hieu Ctrl C thi mot socket se gui só -2 qua server
            if fileNameLength==-2:
                print(f"[INFO] Da ngat ket noi voi {clientAddress}")
                break

            fileName=recvString(socketList[0], fileNameLength)  # Nhan ten cua file can tai



            # Gửi kích thước file
            fileSize = getFileSize(folder+fileName)
            sendNumber(fileSize, socketList[0])


            if fileSize==-1:  # Truong hop file khong ton tai
                continue


            chunkSize=fileSize//4
            chunk=[]

            # Doc file luu vao tung chunk
            with open(folder + fileName, "rb") as f:
                for i in range(3):
                    chunk.append(f.read(chunkSize))
                chunk.append(f.read(fileSize-3*chunkSize))

            # Tao cac ham gui song song
            sender_1 = multiprocessing.Process(target=sendChunk, args=(socketList[0], chunk[0], fileName, clientAddress,))
            sender_2 = multiprocessing.Process(target=sendChunk, args=(socketList[1], chunk[1], fileName, clientAddress,))
            sender_3 = multiprocessing.Process(target=sendChunk, args=(socketList[2], chunk[2], fileName, clientAddress,))
            sender_4 = multiprocessing.Process(target=sendChunk, args=(socketList[3], chunk[3], fileName, clientAddress,))

            # Bat dau gui file
            sender_1.start()
            sender_2.start()
            sender_3.start()
            sender_4.start()




def startServer(serverIP, port, fileList, folder, maxClient):

    # Tao socket chinh va lang nghe cac client
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((serverIP, port))
    server.listen(maxClient)

    print(f"[INFO] Server listening on {serverIP}:{port}\n")


    while True:

        # Tao 4 socket va chap nhan 4 connection
        client_socket=[]
        addr=""
        for i in range(4):
            coon, addr = server.accept()
            client_socket.append(coon)
        print(f"[INFO] Connected to {addr}")


        # Gui thong tin cua danh sach cac file
        sendNumber(getFileSize(fileList), client_socket[0])
        sendString(getFileData(fileList), client_socket[0])

        # Xu li song song cac client
        process = multiprocessing.Process(target=handleClient, args=(client_socket, folder, addr,))
        process.start()
        print(f"[INFO] Active processes: {len(multiprocessing.active_children())}")




if __name__ == "__main__":
    startServer("127.0.0.1", 65432, "Server/fileList.txt", "Server/", 10)
