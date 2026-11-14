
import socket
import threading

HOST = "127.0.0.1"
PORT = 5091

clients = {}  # username -> socket
clients_lock = threading.Lock()


def handle_client(connection, address):
    username = None
    try:
        with connection:
            reader = connection.makefile("r", encoding="utf-8")
            connection.sendall(b"WELCOME Smart Home Server. Enter LOGIN <username>\n")
            for line in reader:
                command = line.strip()
                if not command:
                    connection.sendall(b"ERROR Empty command\n")
                    continue
                if username is None:
                    parts = command.split()
                    if len(parts) != 2 or parts[0].upper() != "LOGIN":
                        connection.sendall(b"ERROR First command must be LOGIN <username>\n")
                        continue
                    proposed = parts[1]
                    with clients_lock:
                        if proposed in clients:
                            accepted = False
                        else:
                            clients[proposed] = connection
                            accepted = True
                            count = len(clients)
                    if not accepted:
                        connection.sendall(b"ERROR Username already in use\n")
                        continue
                    username = proposed
                    print(f"LOGIN {username} from {address}; active clients: {count}")
                    connection.sendall(f"OK Logged in as {username}\n".encode())
                elif command.upper() == "PING":
                    connection.sendall(b"PONG Smart Home Server is running\n")
                elif command.upper() == "LIST":
                    with clients_lock:
                        names = sorted(clients)
                    connection.sendall(f"USERS {', '.join(names)}\n".encode())
                elif command.upper() == "QUIT":
                    connection.sendall(b"BYE\n")
                    break
                else:
                    connection.sendall(b"ERROR Unknown command (use PING, LIST, QUIT)\n")
    except (ConnectionError, OSError, UnicodeDecodeError) as error:
        print(f"Connection ended for {address}: {error}")
    finally:
        if username is not None:
            with clients_lock:
                clients.pop(username, None)
                count = len(clients)
            print(f"DISCONNECT {username}; active clients: {count}")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"Smart Home TCP server listening on {HOST}:{PORT}")
        try:
            while True:
                connection, address = server.accept()
                print(f"CONNECTED {address}")
                threading.Thread(target=handle_client, args=(connection, address), daemon=True).start()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
