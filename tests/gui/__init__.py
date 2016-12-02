import os


class FixturePaths:

    def __init__(self):
        self.gui_tests = os.path.dirname(__file__)
        self.dir = os.path.join(self.gui_tests, "fixtures")
        self.files = dict()
        dir_list = os.listdir(self.dir)
        for entry in dir_list:
            self.files[os.path.basename(entry)] = os.path.join(self.dir, entry)
