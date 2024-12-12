import socket
import os
import time
from multiprocessing import Process, Pipe
from math import floor


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
        if size == 0:
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


def isChange(fileName, oldSize):
    curSize = getFileSize(fileName)
    if curSize == None:
        return False
    return curSize != oldSize


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


def socketRecvDataWithSeq(client, server_address, size, type, ack):
    max_retries = 10
    retries = 0

    while (retries < max_retries):
        packet, _ = client.recvfrom(size + 1024)
        if not packet:
            return None

        _ack = packet.split(b"|", 1)
        if len(_ack) != 2:  # Nếu file nhận là ack thì bỏ qua. Trong trường hợp lệnh sent phía trước bị dư
            continue

        seq_number, checksum, data = packet.split(b"|", 2)
        seq = int(seq_number.decode())

        if (seq == ack + 1 and int(checksum.decode()) == ones_complement_checksum(data)):
            ack += 1
            client.sendto(str(ack).encode(), server_address)
            if not data:
                return None, ack
            if type == 2:
                return data, ack
            if type == 1:
                return int(data.decode()), ack
            else:
                return data.decode(), ack
        else:
            # print(f"[INFO] ERROR seq number {ack}")
            client.sendto(str(ack).encode(), server_address)
            retries += 1


def socketSendDataWithSeq(client, server, data, seq):
    # Nếu không nhận được file ACK sau n lần gửi ta mặc định client đã nhận được. Vì nếu không nhận được hay nhận được rồi thì ta cũng sẽ không tiếp tục gửi.
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

    while (retries < max_retries):
        client.sendto(packet, server)
        client.settimeout(timeout)

        try:
            while True:
                ack_, _ = client.recvfrom(1024)  # Chờ ACK từ server

                _ack = ack_.split(b"|", 1)
                if len(_ack) == 2:  # Nếu file nhận KHÔNG là ack thì bỏ qua. Trong trường hợp file ACK phía trước bị chậm phía trước bị dư
                    continue

                ack_number = int(ack_.decode())

                if ack_number == seq:
                    # print(f"[INFO] ACK received for seq {seq}")
                    break
                else:
                    pass
                    # print(f"[ERROR] Wrong ACK")

            if ack_number == seq:
                break
        except socket.timeout:
            retries += 1

    return seq

    client.settimeout(None)

    if retries == max_retries:
        # print(f"[ERROR] Failed to send seq {seq}")
        return


def split_string(input_string, delimiter):
    # Sử dụng phương thức split() để chia chuỗi theo ký tự phân cách
    result = input_string.strip().split(delimiter)
    return result


def get_num(key, fileList):
    for i in range(len(fileList)):
        if key == fileList[i]:
            return i
    return -1


def printProcess(a, b, c, d, pipe1, pipe2, pipe3, pipe4, fileName):
    msg1 = 0
    msg2 = 0
    msg3 = 0
    msg4 = 0

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
            f"\r[INFO] Downloading {fileName} | Part 1: {msg1}% | Part 2: {msg2}% | Part 3: {msg3}% | Part 4: {msg4}%",
            end="")

        if msg1 >= 100 and msg2 >= 100 and msg3 >= 100 and msg4 >= 100:
            break


def sentRequest(client, server, seq, part, length):
    seq += 1
    packet = f"{seq}|{part}".encode()

    max_retries = 5
    timeout = 2
    retries = 0

    while (retries < max_retries):
        client.sendto(packet, server)
        client.settimeout(timeout)

        try:
            packetReceived, _ = client.recvfrom(2 * 1024)
            if not packetReceived:
                return None

            ack_number, checksum, data = packetReceived.split(b"|", 2)
            ack = int(ack_number.decode())

            if (ack == 0):

                return

            if (seq == ack and int(checksum.decode()) == ones_complement_checksum(data)):
                if not data:

                    return None


                return data


        except socket.timeout:
            retries += 1

    client.settimeout(None)

    if retries == max_retries:

        return None


def receiveChunk(pipe, chunkSize, part, processPipe, server):
    seq = 0
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #client.bind(('localhost', 52370 + part))  ## 54321, 54322, 54323, 54324, 54325
    length = 0
    data = b""

    # print(part)

    while length < chunkSize:
        data += sentRequest(client, server, seq, part, length)
        seq += 1
        # print(f"{length} and {chunkSize}")
        length = len(data)
        progress = floor(length / chunkSize * 100.0)
        # print(progress)
        processPipe.send(progress)

    # print(1)
    sentRequest(client, server, -1, part, length)

    pipe.send(data)
    client.close()


HOST = "172.20.10.3"  # IP adress server
PORT = 65432  # port is used by the server

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = (HOST, PORT)


# client.sendto(b"GET_FILE", server_address)
def start_client():
    try:
        seq = 0
        ack = 0

        seq = socketSendDataWithSeq(client, server_address, "GET_FILE", seq)

        size, ack = socketRecvDataWithSeq(client, server_address, 1024, 1, ack)
        # print(size)
        data, ack = socketRecvDataWithSeq(client, server_address, size, 0, ack)
        print("Danh sach cac file co the download la:")
        fileList = split_string(data, '\n')
        fileSent = []
        fileName = []
        fileSize = []
        for i in range(len(fileList)):
            fileName.append('')
            fileSize.append('')
            fileSent.append(0)
            fileName[i], fileSize[i] = fileList[i].split(' ')
            print(fileName[i], fileSize[i], sep=' ')

        start_time = time.time()
        oldSize = getFileSize("Client/input.txt")
        newSize = 0

        while True:
            if isChange("Client/input.txt", oldSize):

                newSize = getFileSize("Client/input.txt")
                changeSize = newSize - oldSize

                split = split_string(fileData("Client/input.txt"), '\n')
                # print(len(split))

                for i in range(len(split)):
                    if split[i] != "":

                        k = get_num(split[i], fileName)

                        if k == -1:
                            print("Khong ton tai file, vui long kiem tra ten file!")
                            break

                        if fileSent[k] == 1:
                            continue

                        fileSent[k] = 1

                        seq = socketSendDataWithSeq(client, server_address, len(split[i]), seq)
                        seq = socketSendDataWithSeq(client, server_address, split[i], seq)

                        # client1.sendall(b"ACK")  # Gửi phản hồi
                        filesize, ack = socketRecvDataWithSeq(client, server_address, 1024, 1, ack)

                        Des = "Client/" + split[i]

                        chunkSize = filesize // 4

                        output_1, input_1 = Pipe()
                        output_2, input_2 = Pipe()
                        output_3, input_3 = Pipe()
                        output_4, input_4 = Pipe()

                        progress1, p1 = Pipe()
                        progress2, p2 = Pipe()
                        progress3, p3 = Pipe()
                        progress4, p4 = Pipe()

                        length = 0

                        receiver1 = Process(target=receiveChunk,
                                            args=(input_1, chunkSize, 1, p1, server_address))
                        receiver2 = Process(target=receiveChunk,
                                            args=(input_2, chunkSize, 2, p2, server_address))
                        receiver3 = Process(target=receiveChunk,
                                            args=(input_3, chunkSize, 3, p3, server_address))
                        receiver4 = Process(target=receiveChunk,
                                            args=(input_4, filesize - 3 * chunkSize, 4, p4, server_address))
                        processes = [receiver1, receiver2, receiver3, receiver4]

                        for p in processes:
                            # print(1)
                            p.start()

                        printProcess(receiver1, receiver2, receiver3, receiver4, progress1, progress2, progress3,
                                     progress4, split[i])
                        output = [output_1.recv(), output_2.recv(), output_3.recv(), output_4.recv()]

                        for p in processes:
                            p.join()

                        with open("Client/" + split[i], "wb") as f:
                            for data in output:
                                f.write(data)
                            print(f"\n[INFO] Da ghi file {split[i]}")

                        """
                        with open("Client/" + split[i],"wb") as f:
                            while(length < filesize):
                                receiver = socketRecvDataWithSeq(client, server_address, 1024, 2, ack)
                                if not receiver:
                                    break
                                length += len(receiver)
                                print(f"\r[INFO] Downloading {split[i]}: {round((length / filesize) * 100)}%", end = "")
                                f.write(receiver)
                        """
                        ##print("\n")

                oldSize = newSize
            else:
                oldSize = getFileSize("Client/input.txt")
            time.sleep(5)

    except KeyboardInterrupt:
        seq = socketSendDataWithSeq(client, server_address, "FIN", seq)
        client.close()
    finally:
        client.close()


if __name__ == "__main__":
    start_client()