import time

class snowflake:
    def __init__(self, machine_id):
        self.machine_id = machine_id
        self.last_timestamp = 0
        self.sequence = 0

    def generate_id(self):
        timestamp = int(time.time() * 1000)

        if timestamp < self.last_timestamp:
            raise Exception("Invalid System Clock")

        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & 4095
            if self.sequence == 0:
                timestamp = self.wait_next_millis(self.last_timestamp)
        else:
            self.sequence = 0

        self.last_timestamp = timestamp

        return ((timestamp - 1288834974657) << 22) | (self.machine_id << 12) | self.sequence

    def wait_next_millis(self, last_timestamp):
        timestamp = int(time.time() * 1000)
        while timestamp <= last_timestamp:
            timestamp = int(time.time() * 1000)
        return timestamp