import socket
import os
import multiprocessing


def fileData(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()  # Đọc toàn bộ nội dung tệp
        return content
    except FileNotFoundError:
        print(f"Tệp {file_path} không tồn tại.")
        return None

def fileDataFrom(file_path,index):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()  # Đọc toàn bộ nội dung tệp
        return content[index]
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


def sendNumber(num, soc):
    soc.sendall(str(num).encode())

def sendString(string, soc):
    soc.sendall(string.encode('utf-8'))
def sendByte(byte, soc):
    soc.sendall(byte)


def recvNumber(soc, size):
        data = soc.recv(size)
        number = int(data.decode())
        return number

def recvString(soc, size):
        data = soc.recv(size)
        return data.decode()

def writeStringToFile(file_path, content):
        try:
            # Mở tệp ở chế độ ghi ('w'). Nếu tệp đã tồn tại, nó sẽ bị ghi đè.
            with open(file_path, 'a', encoding='utf-8') as file:
                file.write(content)  # Ghi chuỗi vào tệp
            print(f"Đã ghi nội dung vào tệp {file_path}")
        except Exception as e:
            print(f"Lỗi khi ghi tệp: {e}")


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




def handle_client(connection):
    while True:
            length=recvNumber(connection[0],1024) # Nhan do dai cua ten file
            fileName=recvString(connection[0], length)  # Nhan ten cua file can tai


            # Gửi kích thước file
            fileSize = os.path.getsize("Server/" + fileName)
            connection[0].sendall(str(fileSize).encode())

            # Gửi dữ liệu file
            chunkSize=fileSize//4
            chunk=[]
            # Doc file cho tung chunk
            with open("Server/" + fileName, "rb") as f:
                for i in range(3):
                    chunk.append(f.read(chunkSize))
                # Truong hop file size khong chia het cho 4
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







def start_server(host, port,file):

    # Tao socket chinh va lang nghe cac client
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
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
        sendString(fileData(file), client_socket[0])


        process = multiprocessing.Process(target=handle_client, args=(client_socket,))
        process.start()
        print(f"[INFO] Active processes: {len(multiprocessing.active_children())}")




if __name__ == "__main__":
    start_server("127.0.0.1", 65432, "Server/fileList.txt")
