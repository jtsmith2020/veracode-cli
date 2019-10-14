
class Out():
    def __init__(self):
        self.log_level = 0

    def print(self, msg):
        print(msg)

    def log(self, level, msg):
        if level >= self.log_level:
            return
        else:
            output = ""
            if level == 1:
                output = "[VERBOSE] "
            elif level == 2:
                output = "[ DEBUG ] "
            print(output + msg)

    def set_level(self, level):
        self.log_level = level
