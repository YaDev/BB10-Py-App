import tart
import abc


class App(tart.Application):
    def __init__(self, debug=True):
        super().__init__(debug)

    def on_ui_ready(self):
        tart.send("msgFromPython", text="hello, world")