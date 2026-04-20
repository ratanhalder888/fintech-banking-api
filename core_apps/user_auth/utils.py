import random
import socket
import string
import time
from django.conf import settings

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
        self.machine_id = machine_id & 0x3FF   # 10 bits → supports 1024 machines
        self.sequence = 0
        self.last_timestamp = -1

        # Bit layout: [timestamp 41bit][machine 10bit][sequence 12bit]
        self.EPOCH = 1700000000000  # custom epoch (ms)

    def generate(self) -> int:
        timestamp = int(time.time() * 1000) - self.EPOCH

        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & 0xFFF  # 12 bits → 4096/ms
            if self.sequence == 0:
                # Sequence exhausted — wait for next millisecond
                while timestamp <= self.last_timestamp:
                    timestamp = int(time.time() * 1000) - self.EPOCH
        else:
            self.sequence = 0

        self.last_timestamp = timestamp
        return (timestamp << 22) | (self.machine_id << 12) | self.sequence

    

generator = SnowflakeIDGenerator(machine_id=machine_id)

def get_prefix() -> str:
    bank_name = settings.BANK_NAME
    return "".join(word[0] for word in bank_name.split()).upper() or "APP"

def generate_username() -> str:
    prefix = get_prefix()
    snowflake_id = generator.generate()
    return f"{prefix}-{snowflake_id}"

def generate_otp(length=6) -> str:
    return "".join(random.choices(string.digits, k=length))

