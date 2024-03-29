import socket
import time
from getpass import getpass

cmd_sock = None
host = None

not_need_connection = [
    "bye",
    "open",
    "quit"
]

need_connection = [
    "ascii",
    "binary",
    "cd",
    "close",
    "delete",
    "disconnect",
    "get",
    "ls",
    "put",
    "pwd",
    "rename",
    "user"
]


def ftp_send_cmd(socket: socket, str: str): #format string and send to ftp server
    socket.sendall(f"{str}\r\n".encode())
    return

def get_resp(socket: socket) -> str:
    return socket.recv(1024).decode()

def close_cmd_sock():
    global cmd_sock
    try:
        cmd_sock.close()
        cmd_sock = None
        return
    except:
        cmd_sock = None
        return

def ftp_open_data_conn() -> socket:
    global host
    #bind listing socket
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.bind((host, 0))
    data_sock.listen()
    port = data_sock.getsockname()[1] #get port number

    host_part = host.replace('.', ',')
    port = f"{port:016b}" #convert port number to bianry
    port_1 = int(port[0:8], 2) #first part of the port
    port_2 = int(port[8:16], 2) #second part of the port
    ftp_send_cmd(cmd_sock, f"PORT {host_part},{port_1},{port_2}")
    print(get_resp(cmd_sock), end="")
    #TODO: add exception if fail
    return data_sock

def measure(func):
    def wrapper(*args, **kwargs):
        size = 0
        start_time = time.time()

        data, size = func(*args, **kwargs)

        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time == 0: #prevent very fast transfer(start_time = end_time) from causeing devide by 0
            elapsed_time = 0.0001
        
        speed = size / (elapsed_time * 1000)
        status = f"ftp: {size} bytes received in {elapsed_time:.3f}Seconds {speed:.2f}Kbytes/sec."
        return data, status
    return wrapper

@measure
def recv_data(data_sock: socket):
    data_conn, data_addr = data_sock.accept()
    size = 0
    data = ""
    while True:
        data_part = data_conn.recv(1024)
        if data_part:
            data += data_part.decode()
            size += len(data_part)
        else:
            break
    return data, size

def send_data(data_sock):
    data_conn, data_addr = data_sock.accept()



def ascii():
    ftp_send_cmd(cmd_sock, "TYPE A")
    print(get_resp(cmd_sock), end="")
    return

def binary():
    ftp_send_cmd(cmd_sock, "TYPE I")
    print(get_resp(cmd_sock), end="")
    return

def bye():
    try:
        ftp_send_cmd(cmd_sock, "QUIT")
        print(get_resp(cmd_sock), end="")
        close_cmd_sock()
    except:
        pass
    exit()

def cd(remote_dir: str, *argv):
    ftp_send_cmd(cmd_sock, f"CWD {remote_dir}")
    print(get_resp(cmd_sock), end="")
    return

def close():
    try:
        ftp_send_cmd(cmd_sock, "QUIT")
    except:
        print("Not connected.")
        return;

    print(get_resp(cmd_sock), end="")
    close_cmd_sock()
    return

def delete(remote_file: str, *argv):
    ftp_send_cmd(cmd_sock, f"DELE {remote_file}")
    print(get_resp(cmd_sock), end="")
    return

def get(*args):
    return

def ls(remote_dir: str = "", *argv) -> None:
    data_sock = ftp_open_data_conn()

    ftp_send_cmd(cmd_sock, f"NLST {remote_dir}")
    resp = get_resp(cmd_sock)
    resp_code = resp.split()[0]
    print(resp, end='')

    if resp_code == "550": #Couldn't open the file or directory
        return
    elif resp_code != "150":
        print("Unexpected error, ls command")
        return

    data, status = recv_data(data_sock)
    print(data, end="")
    print(get_resp(cmd_sock), end="") #226 Operation successful
    #TODO: add exception
    print(status)
    return

def ftp_open(host_local: str = None, port: str = "21", *argv):
    global cmd_sock
    global host

    if argv:
        print("Usage: open host name [port]")
        return

    if cmd_sock: #check if already connect
        print(f"Already connected to {host}, use disconnect first.")
        return

    cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if not host_local:
        host_local = input("To ")
    
    if not host_local:
        print("Usage: open host name [port]")
        return
    
    #set recieved host from funciton to global var for future use
    host = host_local 

    #attemp establish connection
    try:
        cmd_sock.connect((host_local, int(port)))
    except ConnectionRefusedError:
        print("> ftp: connect :Connection refused")
        close_cmd_sock()
        return
    except socket.timeout:
        print("> ftp: connect :Connection timed out")
        close_cmd_sock()
        return
    except socket.gaierror:
        print(f"Unknown host {host_local}.")
        close_cmd_sock()
        return
    except Exception as e:
        print(type(e).__name__, e.args)
        return

    print(get_resp(cmd_sock), end="")

    #login
    user = input(f"User ({host_local}:(none)): ")
    ftp_send_cmd(cmd_sock, f"USER {user}")

    resp = get_resp(cmd_sock )#respond for username input
    print(resp, end='')
    resp_code = resp.split()[0]

    if resp_code == "501": #missing user argument
        print("Login failed.")
        return
    elif resp_code == "331":
        password = getpass("Password: ")
        cmd_sock.sendall(f"PASS {password}\r\n".encode())
        resp = cmd_sock.recv(1024).decode()
        resp_code = resp.split()[0]
        if resp_code == "530":
            print(resp, end="")
            print("Login failed")
            return
        elif resp_code == "230":
            print(resp, end="")
            return
        else:
            print("unexpected error, password")
            return
    else:
        print("unexpected error, user")
        return


def put(*args):
    return

def pwd():
    ftp_send_cmd(cmd_sock, f"XPWD")
    print(get_resp(cmd_sock), end="")
    return

def rename(from_name: str = "", to_name: str = "", *argv):
    if not from_name: #no argument specify
        from_name = input("From name")
        to_name = input("To name")
    elif not to_name: #only one argument specify
        to_name = input("To name")

    ftp_send_cmd(cmd_sock, f"RNFR {from_name}")
    resp = get_resp(cmd_sock)
    if resp.split()[0] == "350": #directory exists
        print(resp, end="")
        ftp_send_cmd(cmd_sock, f"RNTO {to_name}")
        print(get_resp(cmd_sock), end="")
    else:
        print("Unexpected error, rename command")
    return

def user(*args):
    return


while True:
    input_str = input("ftp> ")

    #input sanitization
    input_list = input_str.split()
    if not input_list: #check for empty command
        continue
    
    command = input_list[0]

    if len(input_list) > 1:
        arg = input_list[1:]
    else:
        arg = ""
    
    if command in not_need_connection:
        match command:
            case "bye":
                bye()

            case "open":
                ftp_open(*arg)

            case "quit":
                bye()

    elif command in need_connection:
        if not cmd_sock:
            print("Not connected.")
            continue

        match command:
            case "ascii":
                ascii()
            
            case "binary":
                binary()
            
            case "cd":
                cd(*arg)

            case "close":
                close()

            case "delete":
                delete(*arg)

            case "disconnect": # disconnect = close
                close()

            case "get":
                get(*arg)

            case "ls":
                ls(*arg)

            case "put":
                put(*arg)

            case "pwd":
                pwd()

            case "rename":
                rename(*arg)

            case "user":
                user(*arg)

    else:
        print("Invalid command.")



#TODO: Command
        #[x] ascii
        #[x] binary
        #[x] bye
        #[x] cd
        #[x] close
        #[x] delete
        #[x] disconnect
        #[ ] get
        #[x] ls
        #[x] open
        #[ ] put
        #[x] pwd
        #[x] quit
        #[x] rename
        #[ ] user

#TODO: features
        #[x] count transfered data
        #[x] speed
        #[x] fix inaccurate speed
        #[x] fix receive data function
        #[x] fix ls function after fix the above
        #[ ] change recv_data func to work with file too
        #[ ] make send_data func.
        #[ ] fix add another print respond for 150 operation successful
        #[ ] add new line when enter password