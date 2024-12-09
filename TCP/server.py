import socket
import os
import multiprocessing


def getFileData(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"[INFO] Tệp {file_path} khong ton tai.")
        return None

def getFileSize(file_path):
    try:
        file_size = os.path.getsize(file_path)  # Lấy kích thước tệp tính theo byte
        return file_size
    except FileNotFoundError:
        print(f"[INFO] Tệp {file_path} khong ton tai.")
        return -1

# Cac ham gui
def sendNumber(num, soc):
    soc.sendall(str(num).encode())
def sendString(string, soc):
    soc.sendall(string.encode('utf-8'))
def sendByte(byte, soc):
    soc.sendall(byte)

# Cac ham nhan
def recvNumber(soc, size):
        number = int(soc.recv(size).decode())
        return number
def recvString(soc, size):
        data = soc.recv(size)
        return data.decode()


def sendChunk(connection, chunk):
    length=len(chunk)
    if length<1024:
        sendByte(chunk,connection)
    else:
        temp=0
        while temp<length:
            first=temp
            last=temp+1024
            if last<length:
                sendByte(chunk[first:last],connection)
            else:
                sendByte(chunk[first:], connection)
            temp+=1024



def handle_client(connection,folder):
    while True:
            length=recvNumber(connection[0],1024) # Nhan do dai cua ten file can tai

            # Khi client nhan tin hieu Ctrl C thi mot socket se gui só -2 qua server
            if length==-2:
                print("[INFO] Da ngat ket noi")
                break

            fileName=recvString(connection[0], length)  # Nhan ten cua file can tai



            # Gửi kích thước file
            fileSize = getFileSize(folder+fileName)
            connection[0].sendall(str(fileSize).encode())

            if fileSize==-1:  # Truong hop file khong ton tai
                break


            chunkSize=fileSize//4
            chunk=[]

            # Doc file cho tung chunk
            with open(folder + fileName, "rb") as f:
                for i in range(3):
                    chunk.append(f.read(chunkSize))
                chunk.append(f.read(fileSize-3*chunkSize))

            # Tao cac ham gui song song
            sender_1 = multiprocessing.Process(target=sendChunk, args=(connection[0], chunk[0],))
            sender_2 = multiprocessing.Process(target=sendChunk, args=(connection[1], chunk[1],))
            sender_3 = multiprocessing.Process(target=sendChunk, args=(connection[2], chunk[2],))
            sender_4 = multiprocessing.Process(target=sendChunk, args=(connection[3], chunk[3],))

            # Bat dau gui file
            sender_1.start()
            sender_2.start()
            sender_3.start()
            sender_4.start()







def start_server(host, port,file,folder,maxClient):

    # Tao socket chinh va lang nghe cac client
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(maxClient)
    print(f"[INFO] Server listening on {host}:{port}\n")


    while True:

        # Tao 4 socket va chap nhan 4 connection
        client_socket=[]
        addr=""
        for i in range(4):
            coon, addr = server.accept()
            client_socket.append(coon)
        print(f"[INFO] Connected to {addr}")


        # Gui thong tin cua danh sach cac file
        sendNumber(getFileSize(file), client_socket[0])
        sendString(getFileData(file), client_socket[0])


        process = multiprocessing.Process(target=handle_client, args=(client_socket,folder,))
        process.start()
        print(f"[INFO] Active processes: {len(multiprocessing.active_children())}")




if __name__ == "__main__":
    start_server("127.0.0.1", 65432, "Server/fileList.txt","Server/",10)
