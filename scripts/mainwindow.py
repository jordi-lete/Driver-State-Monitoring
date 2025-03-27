import sys
from PyQt5.uic import loadUi
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
# from model import Model
import embed_FaceMesh
#from embed_FaceMesh_DMS import Worker

# Class for the main UI
class Ui_Dialog(QMainWindow):
    def __init__(self):
        super(Ui_Dialog, self).__init__()

        loadUi("DrowsinessDetector.ui", self)

        # Worker is the class from the embed_FaceMesh script that displays camera feed
        self.Worker = embed_FaceMesh.Worker()
        self.Worker.start()
        self.Worker.ImageUpdate.connect(self.ImageUpdateSlot)

        self.EAR_slider.valueChanged.connect(self.update_EAR_label)
        self.MAR_slider.valueChanged.connect(self.update_MAR_label)
        self.FAR_lowslider.valueChanged.connect(self.update_FARlow_label)
        self.FAR_upslider.valueChanged.connect(self.update_FARup_label)

        self.resetButton.clicked.connect(self.reset)

        self.updates = embed_FaceMesh.updateValues(self)
        self.updates.start()
        self.calibrateButton.clicked.connect(self.updates.calibrate)
        self.updateButton.clicked.connect(self.updates.update)

        self.FullMeshBox.stateChanged.connect(self.checkbox1)
        self.FeaturesBox.stateChanged.connect(self.checkbox2)

        self.redSlider.valueChanged.connect(self.red)
        self.greenSlider.valueChanged.connect(self.green)
        self.blueSlider.valueChanged.connect(self.blue)

        self.colourLabel.setStyleSheet("background-color:rgb(0,255,0)")


    # Set labels for slider values
    def update_EAR_label(self):
        EARthresh = self.EAR_slider.value()/100
        self.EAR_value.setText(str(EARthresh))
        # Set the thresholds in embed_FaceMesh to the value in the slider
        embed_FaceMesh.Worker.EYE_AR_THRESH = EARthresh
    def update_MAR_label(self):
        MARthresh = self.MAR_slider.value()/100
        self.MAR_value.setText(str(MARthresh))
        # Set the thresholds in embed_FaceMesh to the value in the slider
        embed_FaceMesh.Worker.MOUTH_AR_THRESH = MARthresh
    def update_FARlow_label(self):
        FARlowthresh = self.FAR_lowslider.value()/100
        # Set the maximum for the lower threshold to the value of the upper threshold
        self.FAR_lowslider.setMaximum(self.FAR_upslider.value())
        self.FAR_lowvalue.setText(str(FARlowthresh))
        # Set the thresholds in embed_FaceMesh to the value in the slider
        embed_FaceMesh.Worker.FACE_AR_THRESH_LOWER = FARlowthresh
    def update_FARup_label(self):
        FARupthresh = self.FAR_upslider.value()/100
        # Set the minimum for the upper threshold to the value of the lower threshold
        self.FAR_upslider.setMinimum(self.FAR_lowslider.value())
        self.FAR_upvalue.setText(str(FARupthresh))
        # Set the thresholds in embed_FaceMesh to the value in the slider
        embed_FaceMesh.Worker.FACE_AR_THRESH_UPPER = FARupthresh

    
    def reset(self):
        self.EAR_slider.setValue(30)
        self.MAR_slider.setValue(30)
        self.FAR_upslider.setValue(130)
        self.FAR_upslider.setMinimum(110)
        self.FAR_lowslider.setValue(110)
        self.FAR_lowslider.setMaximum(140)



    def checkbox1(self):
        if self.FullMeshBox.isChecked():
            embed_FaceMesh.Worker.FullFace = "on"
            self.FeaturesBox.setChecked(False)
        elif self.FeaturesBox.isChecked():
            embed_FaceMesh.Worker.FullFace = "off"
        else:
            embed_FaceMesh.Worker.FullFace = "nothing"


    def checkbox2(self):
        if self.FeaturesBox.isChecked():
            embed_FaceMesh.Worker.FullFace = "off"
            self.FullMeshBox.setChecked(False)
        elif self.FullMeshBox.isChecked():
            embed_FaceMesh.Worker.FullFace = "on"
        else:
            embed_FaceMesh.Worker.FullFace = "nothing"


    def red(self):
        embed_FaceMesh.Worker.RED = self.redSlider.value()
        self.colourLabel.setStyleSheet("background-color:rgb("+str(self.redSlider.value())+","+str(self.greenSlider.value())+","+str(self.blueSlider.value())+")")

    def green(self):
        embed_FaceMesh.Worker.GREEN = self.greenSlider.value()
        self.colourLabel.setStyleSheet("background-color:rgb("+str(self.redSlider.value())+","+str(self.greenSlider.value())+","+str(self.blueSlider.value())+")")

    def blue(self):
        embed_FaceMesh.Worker.BLUE = self.blueSlider.value()
        self.colourLabel.setStyleSheet("background-color:rgb("+str(self.redSlider.value())+","+str(self.greenSlider.value())+","+str(self.blueSlider.value())+")")

    
    # Put the camera feed into the "FeedLabel" QLabel
    def ImageUpdateSlot(self, Image):
        self.FeedLabel.setPixmap(QPixmap.fromImage(Image))
        

    # def update(self):
    #     print("start")
    #     self.EAR_slider.setEnabled(True)
    #     self.MAR_slider.setEnabled(True)
    #     self.FAR_lowslider.setEnabled(True)
    #     self.FAR_upslider.setEnabled(True)
    #     self.updateButton.setEnabled(False)
    #     self.calibrateButton.setEnabled(True)

    #     self.EAR_slider.setValue(math.floor(100*Worker.EYE_AR_THRESH_NEW))
    #     self.MAR_slider.setValue(math.floor(100*Worker.MOUTH_AR_THRESH_NEW))
    #     self.EAR_value.setText(str(Worker.EYE_AR_THRESH_NEW))
    #     self.MAR_value.setText(str(Worker.MOUTH_AR_THRESH_NEW))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Ui_Dialog()
    ui.show()
    sys.exit(app.exec_())