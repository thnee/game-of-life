#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import random
from threading import Thread, Lock
import wx

# initual values for the matrix
START_PATTERN = [

    # Blinker (period 2 oscillator)
    [2,1], [2,2], [2,3],

    # Block (still life)
    # [1,1], [1,2], [2,1], [2,2],

    # Glider (space ship)
    # [0,2], [1,3], [2,1], [2,2], [2,3],
]

# cell matrix settings
CELL_MATRIX_SIZE_Y = 40
CELL_MATRIX_SIZE_X = 40

# drawing settings
CELL_SIZE = 10
CELL_MARGIN = 1
SLEEP_TIME = 0.1


# initiate cell matrix
CELL_MATRIX = {}
for y in xrange(CELL_MATRIX_SIZE_Y):
    CELL_MATRIX[y] = {}
    for x in xrange(CELL_MATRIX_SIZE_X):
        CELL_MATRIX[y][x] = 0

# fill cell matrix with start pattern
for i in START_PATTERN:
    CELL_MATRIX[i[0]][i[1]] = 1

cell_lock = Lock()

EVT_DONE = wx.NewId()


class DoneEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_DONE)


class Worker(Thread):
    def __init__(self, redraw, done):
        self.redraw = redraw
        self.done = done

        Thread.__init__(self)

        self._want_abort = False

        self.start()

    def run(self):
        while True:
            if self._want_abort:
                self.done()
                return

            time.sleep(SLEEP_TIME)

            with cell_lock:
                self.work()

            self.redraw()

    def abort(self):
        self._want_abort = True

    def work(self):
        """
        Algorithm for Conway's Game of Life.
        """

        def alive_neighbours(x, y):
            neighbours = []

            # find all neighbouring cells around the given cell
            neighbours.append((x-1, y-1))
            neighbours.append((x-1, y))
            neighbours.append((x-1, y+1))
            neighbours.append((x, y-1))
            neighbours.append((x, y+1))
            neighbours.append((x+1, y-1))
            neighbours.append((x+1, y))
            neighbours.append((x+1, y+1))

            alive_neighbours = 0
            for n in neighbours:
                # if found coordinates are within the matrix
                if (n[0] >= 0 and n[1] >= 0
                and n[0] < CELL_MATRIX_SIZE_X
                and n[1] < CELL_MATRIX_SIZE_Y):
                    # and cell at coordinates is alive
                    if CELL_MATRIX[n[1]][n[0]]:
                        alive_neighbours += 1
            return alive_neighbours

        new_matrix = {}
        for y in CELL_MATRIX:
            new_matrix[y] = CELL_MATRIX[y].copy()

        for y in CELL_MATRIX:
            for x in CELL_MATRIX[y]:
                n = alive_neighbours(x, y)

                # if cell is alive
                if CELL_MATRIX[y][x]:
                    # and number of neighbours cause under-population
                    # or cause cell to be overcrowded
                    if n < 2 or n > 3:
                        # cell dies
                        new_matrix[y][x] = 0

                # if cell is dead
                else:
                    # and number of neighbours support reproduction
                    if n == 3:
                        # cell becomes alive
                        new_matrix[y][x] = 1

        for y in CELL_MATRIX:
            for x in CELL_MATRIX[y]:
                CELL_MATRIX[y][x] = new_matrix[y][x]

    def work_random(self):
        """
        A test worker that generates a random cell matrix.
        May be called in run() instead of work().
        """
        y = random.randint(0, CELL_MATRIX_SIZE_Y-1)
        x = random.randint(0, CELL_MATRIX_SIZE_X-1)

        # invert the value in this position
        if x in CELL_MATRIX[y]:
            value = not CELL_MATRIX[y][x]
        else:
            value = 1

        CELL_MATRIX[y][x] = value


class View(wx.Panel):
    def __init__(self, parent):
        super(View, self).__init__(parent)

        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_size(self, e):
        e.Skip()
        self.Refresh()

    def on_paint(self, e):
        w, h = self.GetClientSize()
        dc = wx.AutoBufferedPaintDC(self)
        dc.Clear()

        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)

        with cell_lock:
            for y in CELL_MATRIX:
                for x in CELL_MATRIX[y]:
                    if CELL_MATRIX[y][x]:
                        dc.SetBrush(wx.Brush(wx.BLACK, wx.SOLID))
                    else:
                        dc.SetBrush(wx.TRANSPARENT_BRUSH)

                    dc.DrawRectangle(
                        (x + 1) * (CELL_SIZE + CELL_MARGIN),
                        (y + 1) * (CELL_SIZE + CELL_MARGIN),
                        CELL_SIZE, CELL_SIZE)

class MainFrame(wx.Frame):
    def __init__(self, parent, id):
        wx.Frame.__init__(self, parent, id)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.SetTitle('life')
        self.view = View(self)

        def redraw():
            self.view.Refresh()

        def done():
            self.Destroy()

        self.worker = Worker(redraw, done)

    def on_close(self, event):
        self.worker.abort()


class MainApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None, -1)
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True


def main():
    app = MainApp(0)
    app.MainLoop()

if __name__ == '__main__':
    main()
