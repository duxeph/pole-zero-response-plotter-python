import os
import sys

try:
    import numpy as np
    from PyQt5.QtWidgets import *
    from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)
except ImportError as e:
    with open(os.getcwd()+"/log.txt", "w") as file:
        file.write(os.popen(f"pip install -r {os.getcwd()}/requirements.txt").read())
    try:
        import numpy as np
        from PyQt5.QtWidgets import *
        from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)
    except ImportError as e:
        print("[EXCEPTION] Something has gone wrong. Please provide requirements.txt before running again.")
        sys.exit()

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QCursor
from PyQt5.uic import loadUi
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)

from numpy import arange, pi, cos, sin, arctan
class plotS:
    def __init__(self, poles, zeros, scale):
        self.poles = poles
        self.zeros = zeros
        self.scale = scale
    def yMax(self, array):
        if len(array)==0: return 0
        max = array[0][1]
        for i in array:
            if max<i[1]:
                max = i[1]
        return max
    def complex_dist(self, x, y):
        return ((y-x[1])**2 + (0-x[0])**2)**(1/2)
    def plot_magnitude_response(self, sensitivity=0.05, color="r"):
        points = []
        max = int(self.yMax(self.zeros+self.poles)*0.15*self.scale)
        if max<1.5: max=1.5
        for point in arange(-max, max, sensitivity):
            a = 1
            for zero in self.zeros:
                a *= self.complex_dist(zero, point)
            for pole in self.poles:
                a /= self.complex_dist(pole, point)
            points.append(a)
        return [arange(-max, max, sensitivity), points]
    def phase_amount(self, x, y):
        range_x = x[0]
        range_y = x[1] - y
        return arctan(range_y/range_x)
    def plot_phase_response(self, sensitivity=0.05, color="r"):
        points = []
        max = int(self.yMax(self.zeros+self.poles)*0.15*self.scale)
        if max<1.5: max=1.5
        for point in arange(-max, max, sensitivity):
            a = 0
            for zero in self.zeros:
                a += self.phase_amount(zero, point)
            for pole in self.poles:
                a -= self.phase_amount(pole, point)
            points.append(a)
        return [arange(-max, max, sensitivity), points]
class plotZ:
    def __init__(self, poles, zeros, scale):
        self.poles = poles
        self.zeros = zeros
        self.scale = scale
    def yMax(self, array):
        if len(array)==0: return 0
        max = array[0][1]
        for i in array:
            if max<i[1]:
                max = i[1]
        return max
    def complex_dist(self, x, y):
        return ((y[1]-x[1])**2 + (y[0]-x[0])**2)**(1/2)
    def plot_magnitude_response(self, sensitivity=0.005, color="r"):
        points = []
        for point in arange(0, 2*pi, sensitivity):
            x = cos(point)
            y = sin(point)
            a = 1
            for zero in self.zeros:
                a *= self.complex_dist(zero, [x, y])
            for pole in self.poles:
                temp = self.complex_dist(pole, [x, y])
                if temp!=0: a /= temp
                else: a /= 1e-400
            points.append(a)
        return [arange(0, 2*pi, sensitivity), points]
    def phase_amount(self, x, y):
        range_x = x[0] - y[0]
        range_y = x[1] - y[1]
        return arctan(range_y/range_x)
    def plot_phase_response(self, sensitivity=0.005, color="r"):
        points = []
        for point in arange(0, 2*pi, sensitivity):
            x = cos(point)
            y = sin(point)
            a = 0
            for zero in self.zeros:
                a += self.phase_amount(zero, [x, y])
            for pole in self.poles:
                a -= self.phase_amount(pole, [x, y])
            points.append(a)
        return [arange(0, 2*pi, sensitivity), points]

class MyApp(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi(os.getcwd()+"/interface/main.ui", self) # self.setWindowTitle("Deneme") # change title

        self.clearButton.clicked.connect(self.clear)
        self.magButton.clicked.connect(self.plotTypeChanged)
        self.phaseButton.clicked.connect(self.plotTypeChanged)
        self.planeButton.clicked.connect(self.planeChanged)
        self.incScButton.clicked.connect(self.incScale)
        self.decScButton.clicked.connect(self.decScale)
        self.incSenButton.clicked.connect(self.incRatio)
        self.decSenButton.clicked.connect(self.decRatio)

        self.splane = True # true: s-plane, false: z-plane
        self.plotType = "magnitude" # magnitude/phase
        self.scaleRate = 1
        self.scale = 10 # 10 for s-plane, 100 for z-plane
        self.delRange = 10/self.scale # deletion range for deletion box & click
        self.sizePole = 4 # cross length: (-4, -4), (-4, 4), (4, -4), (4, 4): -4 to 4 from up to down and from left to right
        self.sizeZero = 7 # circle length: -7/2 to 7/2 from up to down and from left to right
        self.sensitivity = 0.05 # 0.05 for s-plane, 0.005 for z-plane

        # self.begin, self.destination = QPoint(), QPoint()	
        self.historical = [] # ...[-1] is last pole/zero ('s coordinates) added to map
        self.zeros, self.poles = [], [] # added poles/zeros
        self.movestart = False # true when mouse clicked and moves

        # self.fastInitialize()
        # self.draw()

    def planeChanged(self):
        if self.splane:
            self.splane = False
            self.planeLabel.setText("Current plane: z-plane")
        else:
            self.splane = True
            self.planeLabel.setText("Current plane: s-plane")
        self.clear()
    def plotTypeChanged(self):
        if self.magButton.isChecked():
            self.plotType = "magnitude"
        else:
            self.plotType = "phase"
        self.update_graph()
    def incScale(self):
        if self.scaleRate<5: self.scaleRate += self.scaleRate/4
        if self.scaleRate>5: self.scaleRate = 5
        self.scaleLabel.setText("Scale rate: "+str(round(self.scaleRate, 3)))
        self.fastInitialize()
        self.draw()
    def decScale(self):
        if self.scaleRate>0.5: self.scaleRate -= self.scaleRate/4
        if self.scaleRate<0.5: self.scaleRate = 0.5
        self.scaleLabel.setText("Scale rate: "+str(round(self.scaleRate, 3)))
        self.fastInitialize()
        self.draw()
    def incRatio(self):
        self.sensitivity += self.sensitivity/2
        self.ratioInfoLabel.setText("Sensitivity: "+str(round(self.sensitivity, 4)))
        self.update_graph()
    def decRatio(self):
        self.sensitivity -= self.sensitivity/2
        self.ratioInfoLabel.setText("Sensitivity: "+str(round(self.sensitivity, 4)))
        self.update_graph()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(QPoint(), self.pix)
    def update_graph(self):
        if self.plotType=="magnitude":
            if self.splane: x, y = plotS(self.poles, self.zeros, self.scale).plot_magnitude_response(sensitivity=self.sensitivity)
            else: x, y = plotZ(self.poles, self.zeros, self.scale).plot_magnitude_response(sensitivity=self.sensitivity)
        elif self.plotType=="phase":
            if self.splane: x, y = plotS(self.poles, self.zeros, self.scale).plot_phase_response(sensitivity=self.sensitivity)
            else: x, y = plotZ(self.poles, self.zeros, self.scale).plot_phase_response(sensitivity=self.sensitivity)

        self.MplWidget.canvas.axes.clear()
        self.MplWidget.canvas.axes.plot(x, y, color="r") # self.MplWidget.canvas.axes.plot(t, sinus_signal) # second plot
        if self.plotType=="magnitude":
            self.MplWidget.canvas.axes.legend(('Magnitude Response'),loc='upper right')
            if self.splane:
                self.MplWidget.canvas.axes.set_title('s-plane to Magnitude Response')
            else:
                self.MplWidget.canvas.axes.set_title('z-plane to Magnitude Response')
        else:
            self.MplWidget.canvas.axes.legend(('Phase Response'),loc='upper right')
            if self.splane:
                self.MplWidget.canvas.axes.set_title('s-plane to Phase Response')
            else:
                self.MplWidget.canvas.axes.set_title('z-plane to Phase Response')
        self.MplWidget.canvas.draw()

    def fastInitialize(self):
        # QPoint: x, y, length, height
        self.endHeight = self.lineY.height()
        self.middleHeight = int(self.endHeight/2)
        self.endWidth = self.lineX.width()
        self.middleWidth = int(self.endWidth/2)

        if not self.splane:
            self.sensitivity = 0.005
            self.scale = int(100*self.scaleRate)
        else:
            self.sensitivity = 0.05
            self.scale = int(10*self.scaleRate)
        self.delRange = 10/self.scale # deletion range for deletion box & click
    def resizeEvent(self, event):
        self.fastInitialize()
        self.draw()
    def clear(self):
        self.historical = []
        self.zeros, self.poles = [], []
        self.movestart = False

        self.statusBar.showMessage(f"All cleared.")
        self.fastInitialize()
        self.draw()
    def draw(self):
        self.pix = QPixmap(self.rect().size())
        self.pix.fill(Qt.white)
        painter = QPainter(self.pix)
        painter.drawLine(0, self.middleHeight, self.endWidth, self.middleHeight)
        painter.drawLine(self.middleWidth, 0, self.middleWidth, self.endHeight)

        indexFactor = 3

        if self.splane:
            for i in np.arange(self.middleHeight%self.scale, self.endHeight+self.scale+1, self.scale):
                painter.drawLine(self.middleWidth-indexFactor, i, self.middleWidth+indexFactor, i)
            for i in np.arange(self.middleWidth%self.scale, self.endWidth+self.scale+1, self.scale):
                painter.drawLine(i, self.middleHeight-indexFactor, i, self.middleHeight+indexFactor)
        else:
            painter.drawEllipse(self.middleWidth-int(1*self.scale), self.middleHeight-int(1*self.scale), int(2*self.scale), int(2*self.scale))

            for i in np.arange(self.middleHeight%(self.scale/10), self.endHeight+self.scale/10+1, self.scale/10):
                i = int(i)
                if i%self.scale==self.middleHeight%self.scale: indexFactor = int(indexFactor*2)
                painter.drawLine(self.middleWidth-indexFactor, i, self.middleWidth+indexFactor, i)
                if i%self.scale==self.middleHeight%self.scale: indexFactor = int(indexFactor/2)
            for i in np.arange(self.middleWidth%(self.scale/10), self.endWidth+self.scale/10+1, self.scale/10):
                i = int(i)
                if i%self.scale==self.middleWidth%self.scale: indexFactor = int(indexFactor*2)
                painter.drawLine(i, self.middleHeight-indexFactor, i, self.middleHeight+indexFactor)
                if i%self.scale==self.middleWidth%self.scale: indexFactor = int(indexFactor/2)

        for pole in self.poles:
            xx = int(self.scale*pole[0])
            yx = int(self.scale*pole[1])
            x = int(xx + self.middleWidth)
            y = int(-yx + self.middleHeight)
            painter.drawLine(x-self.sizePole, y-self.sizePole, x+self.sizePole, y+self.sizePole) # sol üstten sağ alta
            painter.drawLine(x-self.sizePole, y+self.sizePole, x+self.sizePole, y-self.sizePole) # sol alttan sağ üste
        for zero in self.zeros:
            xx = int(self.scale*zero[0])
            yx = int(self.scale*zero[1])
            x = int(xx + self.middleWidth)
            y = int(-yx + self.middleHeight)
            painter.drawEllipse(x-int(self.sizeZero/2), y-int(self.sizeZero/2), self.sizeZero, self.sizeZero)
        self.update()
        self.update_graph()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if (self.scaleRate<0.5 and delta<0) or (self.scaleRate>5 and delta>0): return

        self.scaleRate += delta/100*self.scaleRate/4
        if self.scaleRate<0.5: self.scaleRate=0.5
        if self.scaleRate>5: self.scaleRate=5
        self.scaleLabel.setText("Scale rate: "+str(round(self.scaleRate, 3)))
        self.fastInitialize()
        self.draw()
    def mouseReleaseEvent(self, event):
        self.movestart = False
        QWidget.setCursor(self, QCursor(Qt.ArrowCursor))
    def mouseMoveEvent(self, event):
        if not self.delBox.isChecked() and (event.buttons()==Qt.LeftButton or event.buttons()==Qt.RightButton) and len(self.historical)>0:
            begin = event.pos()
            x = -self.middleWidth+begin.x() # - toplam genişliğin yarısı + anlık x: x eksenine gerçek menzil
            y = self.middleHeight-begin.y() # toplam uzunluğun yarısı - anlık y: y eksenine gerçek menzil

            if abs(x)>self.middleWidth or abs(y)> self.middleHeight:
                return
            QWidget.setCursor(self, QCursor(Qt.ClosedHandCursor))

            if not self.movestart:
                self.delete([x/self.scale, y/self.scale], draw=False)
                self.movestart = True
            else:
                self.delete(self.historical[-1], draw=False)
            self.add([x/self.scale, y/self.scale], "pole" if event.buttons()==Qt.LeftButton else "zero")
    def mousePressEvent(self, event):
        QWidget.setCursor(self, QCursor(Qt.PointingHandCursor))
        begin = event.pos()
        x = -self.middleWidth+begin.x() # - toplam genişliğin yarısı + anlık x: x eksenine gerçek menzil
        y = self.middleHeight-begin.y() # toplam uzunluğun yarısı - anlık y: y eksenine gerçek menzil

        if self.delBox.isChecked():
            self.delete([x/self.scale, y/self.scale], draw=True)
        elif self.lookFor([x/self.scale, y/self.scale])==False:
            self.movestart = True
            self.add([x/self.scale, y/self.scale], "pole" if event.buttons()==Qt.LeftButton else "zero")

    def lookFor(self, pos):
        for i in self.historical[::-1]:
            if abs(i[0]-pos[0])<self.delRange and (abs(i[1]-pos[1])<self.delRange or abs(i[1]+pos[1])<self.delRange):
                if self.poles.count(i)>0 or self.poles.count([i[0], -i[1]])>0 or self.zeros.count(i)>0 or self.zeros.count([i[0], -i[1]]):
                    return True
        return False
    def delete(self, pos, draw=True):
        for i in self.historical[::-1]:
            if abs(i[0]-pos[0])<self.delRange and (abs(i[1]-pos[1])<self.delRange or abs(i[1]+pos[1])<self.delRange):
                if self.poles.count(i)>0 or self.poles.count([i[0], -i[1]])>0:
                    if i[1]==0: self.poles.remove(i)
                    else: self.poles.remove(i); self.poles.remove([i[0], -i[1]])
                    self.statusBar.showMessage(f"Pole is deleted from ({round(i[0], 2)}, {round(i[1], 2)}). Current case: {'Divergent' if len(self.zeros)>len(self.poles) else 'Convergent'}{' to some constant' if len(self.zeros)==len(self.poles) else ''}. P:{int(len(self.poles))}, Z:{int(len(self.zeros))})")
                elif self.zeros.count(i)>0 or self.zeros.count([i[0], -i[1]]):
                    if i[1]==0: self.zeros.remove(i)
                    else: self.zeros.remove(i); self.zeros.remove([i[0], -i[1]])
                    self.statusBar.showMessage(f"Zero is deleted from ({round(i[0], 2)}, {round(i[1], 2)}). Current case: {'Divergent' if len(self.zeros)>len(self.poles) else 'Convergent'}{' to some constant' if len(self.zeros)==len(self.poles) else ''}. P:{int(len(self.poles))}, Z:{int(len(self.zeros))})")
                else:
                    print("[EXCEPTION] Something has gone wrong. Please contact the developer (contact e-mail: furieuxx13@gmail.com).")
                self.historical.remove(i)
                break
        if draw: self.draw()
    def add(self, pos, case, draw=True):
        if abs(pos[0])>self.middleWidth/self.scale or abs(pos[1])>self.middleHeight/self.scale:
            self.movestart = False
            return
        if -5/self.scale<pos[1]<5/self.scale: pos[1] = 0
        if -5/self.scale<pos[0]<5/self.scale: pos[0] = 0
        self.historical.append(pos)
        if case=="pole":
            if pos[1]==0: self.poles.append(pos)
            else: self.poles.append(pos); self.poles.append([pos[0], -pos[1]])
            self.statusBar.showMessage(f"Pole is added to ({round(pos[0], 2)}, {round(pos[1], 2)}). Current case: {'Divergent' if len(self.zeros)>len(self.poles) else 'Convergent'}{' to some constant' if len(self.zeros)==len(self.poles) else ''}. P:{int(len(self.poles))}, Z:{int(len(self.zeros))}")
        elif case=="zero":
            if pos[1]==0: self.zeros.append(pos)
            else: self.zeros.append(pos); self.zeros.append([pos[0], -pos[-1]])
            self.statusBar.showMessage(f"Zero is added to ({round(pos[0], 2)}, {round(pos[1], 2)}). Current case: {'Divergent' if len(self.zeros)>len(self.poles) else 'Convergent'}{' to some constant' if len(self.zeros)==len(self.poles) else ''}. P:{int(len(self.poles))}, Z:{int(len(self.zeros))}")
        if draw: self.draw()



# CONTROL
class StartApp(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        loadUi(os.getcwd()+"/interface/startpanel.ui", self) # self.setWindowTitle("Deneme") # change title

        self.startButton.clicked.connect(self.start)
        self.exitButton.clicked.connect(sys.exit)

        self.initialize()

    def initialize(self):
        self.startButton.setEnabled(True)
        self.infoLabel.setText("Welcome. You can start freely.")
        self.keyText.setEnabled(False)
        self.enabled_to_use = 1 # program açılabilir

    def start(self):
        self.close()
        print(f"Welcome! For any recommendations, please contact the owner! Happy EEM301 studies!")
        try:
            self.plot = MyApp()
            self.plot.show()

            self.plot.fastInitialize()
            self.plot.draw()
        except Exception as e:
            print("[EXCEPTION:404] Something has gone wrong. Please contact and send following error message to developer:", e)

app = QApplication([])
# window = MyApp()
window = StartApp()
window.show()
app.exec_()