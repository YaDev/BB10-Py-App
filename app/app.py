import tart


class App(tart.Application):
    def __init__(self, debug=True):
        super().__init__(debug)

    def ui_ready(self):
        tart.send("msgFromPython", text="hello, world")
