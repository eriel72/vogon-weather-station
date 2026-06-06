import ujson

RAIN_FILE = "rain.json"

class RainState:
    def __init__(self):
        self.rain_count = 0
        self.dirty = False

    def load(self):
        try:
            with open(RAIN_FILE) as f:
                data = ujson.loads(f.read())
                self.rain_count = data.get("rain_count", 0)
        except:
            self.rain_count = 0

    def add_tip(self):
        self.rain_count += 1
        self.dirty = True

    def mm(self, mm_per_tip):
        return self.rain_count * mm_per_tip

    def save(self):
        if not self.dirty:
            return

        tmp = {"rain_count": self.rain_count}

        # safe write (minskar risk för korrupt fil)
        with open(RAIN_FILE, "w") as f:
            f.write(ujson.dumps(tmp))
            f.flush()

        self.dirty = False