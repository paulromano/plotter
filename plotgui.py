#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, openmc, copy
from collections import defaultdict
from PySide2 import QtCore, QtGui
from PySide2.QtWidgets import (QWidget, QPushButton, QHBoxLayout, QVBoxLayout,
    QApplication, QGroupBox, QFormLayout, QLabel, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QSizePolicy, QSpacerItem, QMainWindow,
    QCheckBox, QScrollArea, QLayout, QRubberBand, QMenu, QAction, QMenuBar,
    QFileDialog)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Set Window Title
        self.setWindowTitle('OpenMC Plot Explorer')

        # Create Menubar
        self.createMenuBar()

        # Create Layout:
        self.createLayout()

        # Create, set main widget
        self.mainWidget = QWidget()
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

        self.currentPlot = {'xOr': 0.0, 'yOr': 0.0, 'zOr': 0.0,
                            'colorby': 'material', 'basis': 'xy',
                            'width': 25.0, 'height': 25.0, 'hRes': 500,
                            'vRes': 500}
        self.previousPlots = []
        self.subsequentPlots = []

        # Load Plot
        self.updatePlot()

    def createMenuBar(self):

        # Actions
        self.saveAction = QAction("&Save Image As...", self)
        self.saveAction.setShortcut("Ctrl+S")
        self.saveAction.triggered.connect(self.saveImage)

        self.applyAction = QAction("&Apply Changes", self)
        self.applyAction.setShortcut("Shift+Return")
        self.applyAction.triggered.connect(self.applyChanges)

        self.undoAction = QAction('&Undo', self)
        self.undoAction.setShortcut("Ctrl+Z")
        self.undoAction.setDisabled(True)
        self.undoAction.triggered.connect(self.undo)

        self.redoAction = QAction('&Redo', self)
        self.redoAction.setDisabled(True)
        self.redoAction.setShortcut("Ctrl+Shift+Z")
        self.redoAction.triggered.connect(self.redo)

        # Menus
        self.mainMenu = self.menuBar()
        #self.mainMenu.setNativeMenuBar(False)
        self.fileMenu = self.mainMenu.addMenu('&File')
        self.editMenu = self.mainMenu.addMenu('&Edit')
        self.fileMenu.addAction(self.saveAction)
        self.editMenu.addAction(self.applyAction)
        self.editMenu.addAction(self.undoAction)
        self.editMenu.addAction(self.redoAction)

    def saveImage(self):
        filename, ext = QFileDialog.getSaveFileName(self, "Save Plot Image",
                                                    "", "Images (*.png *.ppm)")
        if filename:
            if "." not in filename:
                self.pixmap.save(filename + ".ppm")
            else:
                self.pixmap.save(filename)
        else: pass

    def undo(self):
        self.subsequentPlots.append(copy.deepcopy(self.currentPlot))
        self.currentPlot = self.previousPlots.pop()

        self.revertControls()
        self.updatePlot()

        if not self.previousPlots:
            self.undoAction.setDisabled(True)

        self.redoAction.setDisabled(False)

    def redo(self):
        self.previousPlots.append(copy.deepcopy(self.currentPlot))
        self.currentPlot = self.subsequentPlots.pop()
        self.revertControls()
        self.updatePlot()

        if not self.subsequentPlots:
            self.redoAction.setDisabled(True)

        self.undoAction.setDisabled(False)

    def revertControls(self):

        self.xOr.setText(str(self.currentPlot['xOr']))
        self.yOr.setText(str(self.currentPlot['yOr']))
        self.zOr.setText(str(self.currentPlot['zOr']))
        self.colorby.setCurrentText(self.currentPlot['colorby'])
        self.basis.setCurrentText(self.currentPlot['basis'])
        self.width.setValue(self.currentPlot['width'])
        self.height.setValue(self.currentPlot['height'])
        self.hRes.setValue(self.currentPlot['hRes'])
        self.vRes.setValue(self.currentPlot['vRes'])

    def showCurrentPlot(self):
        cp = self.currentPlot
        self.statusBar().showMessage(f"Origin: ({cp['xOr']}, {cp['yOr']}, "
            f"{cp['zOr']})  |  Width: {cp['width']} Height: {cp['height']}  |"
            f"  Color By: {cp['colorby']}  |  Basis: {cp['basis']}")

    def applyChanges(self):

        previous = copy.deepcopy(self.currentPlot)

        # Convert origin values to float
        for value in [self.xOr, self.yOr, self.zOr]:
            try:
                value.setText(str(float(value.text().replace(",", ""))))
            except ValueError:
                value.setText('0.0')

        # Create dict of current plot values
        self.currentPlot['xOr'] = float(self.xOr.text())
        self.currentPlot['yOr'] = float(self.yOr.text())
        self.currentPlot['zOr'] = float(self.zOr.text())
        self.currentPlot['colorby'] = self.colorby.currentText()
        self.currentPlot['basis'] = self.basis.currentText()
        self.currentPlot['width'] = self.width.value()
        self.currentPlot['height'] = self.height.value()
        self.currentPlot['hRes'] = self.hRes.value()
        self.currentPlot['vRes'] = self.vRes.value()

        if self.currentPlot != previous:
            self.previousPlots.append(previous)
            self.updatePlot()
            self.subsequentPlots = []

    def updatePlot(self):

        cp = self.currentPlot

        # Generate plot.xml
        plot = openmc.Plot()
        plot.filename = 'plot'
        plot.color_by = cp['colorby']
        plot.basis = cp['basis']
        plot.origin = (cp['xOr'], cp['yOr'], cp['zOr'])
        plot.width = (cp['width'], cp['height'])
        plot.pixels = (cp['hRes'], cp['vRes'])
        plot.background = 'black'

        plots = openmc.Plots([plot])
        plots.export_to_xml()
        openmc.plot_geometry()

        # Update plot image
        self.pixmap = QtGui.QPixmap('plot.ppm')
        self.plotIm.setPixmap(self.pixmap)
        self.plotIm.adjustSize()

        if self.previousPlots:
            self.undoAction.setDisabled(False)

        if self.subsequentPlots:
            self.redoAction.setDisabled(False)

        # Get screen dimensions
        self.screen = app.desktop().screenGeometry()
        self.setMaximumSize(self.screen.width(), self.screen.height())

        # Adjust scroll area to fit plot if window will not exeed screen size
        if self.hRes.value() < .8 * self.screen.width():
            self.frame.setMinimumWidth(self.plotIm.width() + 20)
        else:
            self.frame.setMinimumWidth(20)
        if self.vRes.value() < .85 * self.screen.height():
            self.frame.setMinimumHeight(self.plotIm.height() + 20)
        else:
            self.frame.setMinimumHeight(20)

        # Update status bar
        self.showCurrentPlot()

        # Determine Scale of image / plot
        self.plotIm.scale = (self.hRes.value() / self.width.value(),
                           self.vRes.value() / self.height.value())

        # Determine image axis relative to plot
        if self.basis.currentText()[0] == 'x':
            self.plotIm.imageX = ('xOr', self.xOr)
        else:
            self.plotIm.imageX = ('yOr', self.yOr)
        if self.basis.currentText()[1] == 'y':
            self.plotIm.imageY = ('yOr', self.yOr)
        else:
            self.plotIm.imageY = ('zOr', self.zOr)

    def onAspectLockChange(self, state):
        if state == QtCore.Qt.Checked:
            self.onRatioChange()
            self.vRes.setDisabled(True)
            self.vResLabel.setDisabled(True)
        else:
            self.vRes.setDisabled(False)
            self.vResLabel.setDisabled(False)

    def onRatioChange(self):
        if self.ratioCheck.isChecked():
            ratio = self.width.value() / self.height.value()
            self.vRes.setValue(int(self.hRes.value() / ratio))

    def createLayout(self):

        # Plot
        self.plotIm = PlotImage()

        # Scroll Area
        self.frame = QScrollArea(self)
        self.frame.setAlignment(QtCore.Qt.AlignCenter)
        self.frame.setWidget(self.plotIm)
        self.frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create Controls
        self.createOriginBox()
        self.createOptionsBox()
        self.createResolutionBox()

        # Create submit button
        self.submitButton = QPushButton("Apply Changes", self)
        self.submitButton.clicked.connect(self.applyChanges)

        # Create control Layout
        self.controlLayout = QVBoxLayout()
        self.controlLayout.addWidget(self.originGroupBox)
        self.controlLayout.addWidget(self.optionsGroupBox)
        self.controlLayout.addWidget(self.resGroupBox)
        self.controlLayout.addWidget(self.submitButton)
        self.controlLayout.addStretch()

        # Create main Layout
        self.mainLayout = QHBoxLayout()
        self.mainLayout.addWidget(self.frame, 1)
        self.mainLayout.addLayout(self.controlLayout, 0)
        self.setLayout(self.mainLayout)

    def createOriginBox(self):

        # X Origin
        self.xOr = QLineEdit()
        self.xOr.setValidator(QtGui.QDoubleValidator())
        self.xOr.setText('0.00')
        self.xOr.setPlaceholderText('0.00')

        # Y Origin
        self.yOr = QLineEdit()
        self.yOr.setValidator(QtGui.QDoubleValidator())
        self.yOr.setText('0.00')
        self.yOr.setPlaceholderText('0.00')

        # Z Origin
        self.zOr = QLineEdit()
        self.zOr.setValidator(QtGui.QDoubleValidator())
        self.zOr.setText('0.00')
        self.zOr.setPlaceholderText('0.00')

        # Origin Form Layout
        self.orLayout = QFormLayout()
        self.orLayout.addRow('X:', self.xOr)
        self.orLayout.addRow('Y:', self.yOr)
        self.orLayout.addRow('Z:', self.zOr)
        self.orLayout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # Origin Group Box
        self.originGroupBox = QGroupBox('ORIGIN')
        self.originGroupBox.setLayout(self.orLayout)

    def createOptionsBox(self):

        # Width
        self.width = QDoubleSpinBox(self)
        self.width.setValue(25)
        self.width.setRange(.1, 10000000)
        self.width.valueChanged.connect(self.onRatioChange)

        # Height
        self.height = QDoubleSpinBox(self)
        self.height.setValue(25)
        self.height.setRange(.1, 10000000)
        self.height.valueChanged.connect(self.onRatioChange)

        # ColorBy
        self.colorby = QComboBox(self)
        self.colorby.addItem("material")
        self.colorby.addItem("cell")

        # Basis
        self.basis = QComboBox(self)
        self.basis.addItem("xy")
        self.basis.addItem("xz")
        self.basis.addItem("yz")

        # Options Form Layout
        self.opLayout = QFormLayout()
        self.opLayout.addRow('Width:', self.width)
        self.opLayout.addRow('Height', self.height)
        self.opLayout.addRow('Color By:', self.colorby)
        self.opLayout.addRow('Basis', self.basis)
        self.opLayout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # Options Group Box
        self.optionsGroupBox = QGroupBox('OPTIONS')
        self.optionsGroupBox.setLayout(self.opLayout)

    def createResolutionBox(self):

        # Horizontal Resolution
        self.hRes = QSpinBox(self)
        self.hRes.setRange(1, 10000000)
        self.hRes.setValue(500)
        self.hRes.setSingleStep(25)
        self.hRes.valueChanged.connect(self.onRatioChange)

        # Vertical Resolution
        self.vResLabel = QLabel('Pixel Height')
        self.vResLabel.setDisabled(True)
        self.vRes = QSpinBox(self)
        self.vRes.setRange(1, 10000000)
        self.vRes.setValue(500)
        self.vRes.setSingleStep(25)
        self.vRes.setDisabled(True)

        # Ratio checkbox
        self.ratioCheck = QCheckBox("Fixed Aspect Ratio", self)
        self.ratioCheck.toggle()
        self.ratioCheck.stateChanged.connect(self.onAspectLockChange)

        # Resolution Form Layout
        self.resLayout = QFormLayout()
        self.resLayout.addRow(self.ratioCheck)
        self.resLayout.addRow('Pixel Width:', self.hRes)
        self.resLayout.addRow(self.vResLabel, self.vRes)
        self.resLayout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # Resolution Group Box
        self.resGroupBox = QGroupBox("RESOLUTION")
        self.resGroupBox.setLayout(self.resLayout)


class PlotImage(QLabel):
    def __init__(self):
        super(PlotImage, self).__init__()

        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMouseTracking(True)

        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QtCore.QPoint()
        self.scale = (1, 1)

    def enterEvent(self, event):
        self.setCursor(QtCore.Qt.CrossCursor)

    def leaveEvent(self, event):
        mainWindow.showCurrentPlot()

    def mousePressEvent(self, event):

        cp = mainWindow.currentPlot

        # Cursor position in pixels relative to center of plot image
        xPos = event.pos().x() - (cp['hRes'] / 2)
        yPos = -event.pos().y() + (cp['vRes'] / 2)

        # Curson position in plot units relative to model
        self.xBandOrigin = (xPos / self.scale[0]) + cp[self.imageX[0]]
        self.yBandOrigin = (yPos / self.scale[1]) + cp[self.imageY[0]]

        # Create rubber band
        self.rubberBand.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))

        # Rubber band start position
        self.origin = event.pos()

        QLabel.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):

        cp = mainWindow.currentPlot

        # Cursor position in pixels relative to center of image
        xPos = event.pos().x() - (cp['hRes'] / 2) #+ 1
        yPos = (-event.pos().y() + (cp['vRes'] / 2)) #+ 1

        # Cursor position in plot units relative to model
        xPlotPos = (xPos / self.scale[0]) + cp[self.imageX[0]]
        yPlotPos = (yPos / self.scale[1]) + cp[self.imageY[0]]

        # Show Cursor position relative to plot in status bar
        if mainWindow.basis.currentText() == 'xy':
            mainWindow.statusBar().showMessage(f"Plot Position: "
                f"({round(xPlotPos, 2)}, {round(yPlotPos, 2)}, {cp['zOr']})")
        elif mainWindow.basis.currentText() == 'xz':
            mainWindow.statusBar().showMessage(f"Plot Position: "
                f"({round(xPlotPos, 2)}, {cp['yOr']}, {round(yPlotPos, 2)})")
        else:
            mainWindow.statusBar().showMessage(f"Plot Position: "
                f"({cp['xOr']}, {round(xPlotPos, 2)}, {round(yPlotPos, 2)})")

        # Update rubber band and values if mouse button held down
        if app.mouseButtons() in [QtCore.Qt.LeftButton, QtCore.Qt.RightButton]:
            self.rubberBand.setGeometry(
                QtCore.QRect(self.origin, event.pos()).normalized())

            # Show rubber band if at least one dimension > 5 pixels
            if self.rubberBand.width() > 5 or self.rubberBand.height() > 5:
                self.rubberBand.show()

            # Update plot X Origin
            xcenter = self.xBandOrigin + ((xPlotPos - self.xBandOrigin) / 2)
            self.imageX[1].setText(str(round(xcenter, 9)))

            # Update plot Y Origin
            ycenter = self.yBandOrigin + ((yPlotPos - self.yBandOrigin) / 2)
            self.imageY[1].setText(str(round(ycenter, 9)))

            # Zoom in to rubber band rectangle if left button held
            if app.mouseButtons() == QtCore.Qt.LeftButton:

                # Update width and height
                mainWindow.width.setValue(abs(self.xBandOrigin - xPlotPos))
                mainWindow.height.setValue(abs(self.yBandOrigin - yPlotPos))

            # Zoom out if right button held. Larger rectangle = more zoomed out
            elif app.mouseButtons() == QtCore.Qt.RightButton:

                # Update width
                width = cp['width'] * (1 + (abs(self.origin.x()
                                    - event.pos().x()) / cp['hRes']) * 4)
                mainWindow.width.setValue(width)

                # Update height
                height = cp['height'] * (1 + (abs(self.origin.y()
                                    - event.pos().y()) / cp['vRes']) * 4)
                mainWindow.height.setValue(height)

    def mouseReleaseEvent(self, event):
        if self.rubberBand.isVisible():
            self.rubberBand.hide()
            mainWindow.applyChanges()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
