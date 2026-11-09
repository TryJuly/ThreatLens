import asyncio
import os

import asyncssh

from common.logger import log_event

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "2222"))
HOST_KEY_PATH = os.environ.get("HOST_KEY_PATH", "data/ssh_host_key")

class SSHHoneypot(asyncssh.SSHServer):
    def connection_made(self, conn):
        self.conn = conn
        self.ip, self.port = conn.get_extra_info('peername')[:2]
        log_event(sensor="ssh_honeypot", event="connect", src_ip=self.ip, src_port=self.port)

    def begin_auth(self, username):
        return True  # Allow authentication attempts

    def password_auth_supported(self):
        return True  # Support password authentication

    def validate_password(self, username, password):
        log_event(sensor="ssh_honeypot", event="login_attempt", src_ip=self.ip, src_port=self.port,
                  username=username, password=password,
                  client_version=self.conn.get_extra_info("client_version"))
        return False  # Always fail authentication

async def main():
    if not os.path.exists(HOST_KEY_PATH):
        os.makedirs(os.path.dirname(HOST_KEY_PATH) or ".", exist_ok=True)
        asyncssh.generate_private_key("ssh-rsa").write_private_key(HOST_KEY_PATH)
        os.chmod(HOST_KEY_PATH, 0o600)

    await asyncssh.create_server(
        SSHHoneypot, HOST, PORT,
        server_host_keys=[HOST_KEY_PATH],
        server_version="OpenSSH_8.9p1 Ubuntu-3ubuntu0.6",
    )
    print(f"Honeypot SSH en écoute sur {HOST}:{PORT}")
    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())