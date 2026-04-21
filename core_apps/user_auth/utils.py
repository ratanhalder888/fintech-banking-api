import threading
import random
import socket
import string
import time
from django.conf import settings


def generate_otp(length=6) -> str:
    return "".join(random.choices(string.digits, k=length))


def get_machine_id() -> int:
    try:
        ip = socket.gethostbyname(socket.gethostname())
        parts = ip.split('.')
        return (int(parts[2]) * 256 + int(parts[3])) % 1024
    except Exception:
        return 1


machine_id = get_machine_id()

class SnowflakeIDGenerator:
    def __init__(self, machine_id: int):
        assert 0 <= machine_id < 1024, "machine_id must be 0–1023"
        self.machine_id = machine_id
        self.sequence = 0
        self.last_timestamp = -1
        self.EPOCH = 1700000000000
        self._lock = threading.Lock()

    def _now(self):
        return int(time.time() * 1000) - self.EPOCH

    def generate(self) -> int:
        with self._lock:
            timestamp = self._now()

            # Clock went backward — handle it
            if timestamp < self.last_timestamp:
                drift = self.last_timestamp - timestamp
                if drift <= 5:  # small drift → just wait
                    time.sleep(drift / 1000.0)
                    timestamp = self._now()
                else:    # large drift → hard fail                  
                    raise RuntimeError(f"Clock drifted back {drift}ms")

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & 0xFFF
                if self.sequence == 0:
                    while timestamp <= self.last_timestamp:
                        timestamp = self._now()
            else:
                self.sequence = 0

            self.last_timestamp = timestamp
            return (timestamp << 22) | (self.machine_id << 12) | self.sequence

    
# singletone generator
_generator = SnowflakeIDGenerator(machine_id=machine_id)

def get_prefix() -> str:
    bank_name = settings.BANK_NAME
    return "".join(word[0] for word in bank_name.split()).upper() or "APP"

def generate_username() -> str:
    prefix = get_prefix()
    snowflake_id = _generator.generate()
    return f"{prefix}-{snowflake_id}"

