import asyncio, os
import asyncssh
from common.logger import log_event

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 2222))

class SSHHoneypot(asyncssh.SSHServer):
    def connection_made(self, conn):
        self.conn = conn
        self.ip, self.port = conn.get_extra_info('peername')[:2]
        log_event(sensor="ssh_honeypot", event="connect", ip=self.ip, port=self.port)

    def begin_auth(self, username):
        return True  # Allow authentication attempts

    def password_auth_supported(self):
        return True  # Support password authentication

    def validate_password(self, username, password):
        log_event(sensor="ssh", event="login_attempt", src_ip=self.ip,
                  username=username, password=password,
                  client_version=self.conn.get_extra_info("client_version"))
        return False  # Always fail authentication

async def main():
    await asyncssh.create_server(
        SSHHoneypot, HOST, PORT,
        server_host_keys=["data/ssh_host_key"],
        server_version="OpenSSH_8.9p1 Ubuntu-3ubuntu0.6",
    )
    print(f"Honeypot SSH en écoute sur {HOST}:{PORT}")
    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())