import colorsys
from PyQt5.uic import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import cv2
import matplotlib
import mediapipe as mp
import time
from scipy.spatial import distance as dist
import pyttsx3
import threading


# Define a class for audio alert. Threaded so that it runs in parallel
class _TTS(threading.Thread):
    # Initialise the class
    def __init__(self):
        self.voice = pyttsx3.init()

    # Define the tts function. Plays the audio when called
    def voice_notification(self, text_):
        self.voice.say(text_)
        self.voice.runAndWait()

    # This function ends current text loops and runs a new one
    def run(self, text_):
        # If the voice is already in loop end it so that a new one can be started.
        if self.voice._inLoop:
            self.voice.endLoop()
        t = threading.Thread(target=self.voice_notification, args=(text_,))
        t.start()


# Class for the video stream and face mesh
class Worker(QThread):
    ImageUpdate = pyqtSignal(QImage)

    # THRESHOLDS - IF FACIAL LANDMARKS LIE OUTSIDE ONE OF THESE RANGES, THE ALARM WILL SOUND
    # THESE VALUES WILL UPDATE WITH SLIDER VALUES
    # Threshold for eye's closing
    EYE_AR_THRESH = 0.3
    # Threshold for mouth opening
    MOUTH_AR_THRESH = 0.3
    # Threshold for looking up or down
    FACE_AR_THRESH_LOWER = 1.1
    # Threshold for looking away to left or right
    FACE_AR_THRESH_UPPER = 1.3

    FullFace = "off"
    CALIBRATE = False
    DONE = False

    RED = 0
    GREEN = 255
    BLUE = 0


    # Define a function that draws the key landmarks
    def draw_landmarks(self, frame, landmarks):
        # image height, image width, image channels
        ih, iw, ic = frame.shape        
        # Loop through each individual landmark
        for faceLms in landmarks:
            point = self.results.multi_face_landmarks[0].landmark[faceLms]
            # Retrieve x and y coordinates
            point_scale = ((int)(point.x*iw), (int)(point.y*ih))
            cv2.circle(frame, point_scale, 1, (self.BLUE,self.GREEN,self.RED), -1)

    # Define a function that calculates EAR and MAR
    def aspect_ratio(self, vert, horiz, frame):
        # image height, image width, image channels
        ih, iw, ic = frame.shape
        face = self.results.multi_face_landmarks[0]

        top = face.landmark[vert[0]]
        bottom = face.landmark[vert[1]]
        top_scaled = ((int)(top.x*iw), (int)(top.y*ih))
        bottom_scaled = ((int)(bottom.x*iw), (int)(bottom.y*ih))
        # compute the euclidean distances between the two sets of vertical eye landmarks (x, y)-coordinates
        A = dist.euclidean(top_scaled, bottom_scaled)

        left = face.landmark[horiz[0]]
        right = face.landmark[horiz[1]]
        left_scaled = ((int)(left.x*iw), (int)(left.y*ih))
        right_scaled = ((int)(right.x*iw), (int)(right.y*ih))
        # compute the euclidean distance between the horizontal eye landmark (x, y)-coordinates
        C = dist.euclidean(left_scaled, right_scaled)

        # compute the eye aspect ratio
        ear = A / C
        return ear

    # Define the function to run the video stream and show the face mesh
    @pyqtSlot()
    def run(self):
        self.ThreadActive = True
        print("[INFO] starting video stream thread...")

        # Video stream using opencv package. In this case we input the connected camera (1)
        self.capture = cv2.VideoCapture(1)
        time.sleep(1.0)
        
        # Number of faces to look for
        self.NUM_FACE = 1    

        # initialise the frame counter as well as a boolean used to indicate if the alarm is going off
        self.COUNTER= 0
        self.ALARM_ON = False
        self.CALIBRATION_COUNTER = 0
        self.FIRST_EAR_IT = True
        self.FIRST_MAR_IT = True


        # Number of frames the AR's must be outside threshold before alarm triggered
        self.CONSEC_FRAMES = 48    
        # Initialise parameters for calibration
        self.interval = 200
        self.Base_EAR = 0
        self.Base_MAR = 0

        
        # Draw the facial points using the mediapipe package
        self.mpDraw = mp.solutions.drawing_utils
        # Control thickness of lines and points

        # Create the face mesh
        self.mpFaceMesh = mp.solutions.face_mesh
        self.mpFaceConnections = mp.solutions.face_mesh_connections.FACEMESH_TESSELATION
        self.faceMesh = self.mpFaceMesh.FaceMesh(max_num_faces=self.NUM_FACE)


        # Landmark indexes for Face, Lips, and eyes in mediapipe package
        self.Face = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
        self.Lips = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 185, 40, 39, 37, 0, 267, 269, 270, 409, 415, 310, 311, 312, 13, 82, 81, 42, 183, 78]
        self.Right_Eye = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.Left_Eye = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]

        # Landmark indexes for AR calculations
        self.Right_Eye_Left_Right = [133, 33]
        self.Right_Eye_Top_Bottom = [159, 145]
        self.Left_Eye_Left_Right = [263, 362]
        self.Left_Eye_Top_Bottom = [386, 374]
        self.Lips_Left_Right = [78, 308]
        self.Lips_Top_Bottom = [13, 14]

        # Landmark indices for face direction. The left, right, top, and bottom most points on the outside of the face
        self.Face_Left_Right = [234, 454]
        self.Face_Top_Bottom = [10, 152]

        # Initialise the text to speak class
        tts = _TTS()

        # Each time the frame updates
        while self.ThreadActive:
            # Read the frame
            ret, frame = self.capture.read()
            if self.CALIBRATE:
                self.CALIBRATION_COUNTER += 1
            # If no issues reading the frame
            if ret:
                # Convert to RGB as this is the only format that mediapipe faceMesh can process
                Image = cv2.cvtColor(frame, cv2.COLOR_HLS2RGB)
                # Process the image
                self.results = self.faceMesh.process(Image)

                # Display the mesh
                # If a face is detected
                if self.results.multi_face_landmarks:

                    if self.FullFace == "off":
                        # Draw Features using the draw_landmarks function defined earlier
                        self.draw_landmarks(frame, self.Lips)
                        self.draw_landmarks(frame, self.Right_Eye)
                        self.draw_landmarks(frame, self.Left_Eye)
                        self.draw_landmarks(frame, self.Face)
                    elif self.FullFace == "on":
                        # FOR THE WHOLE FACE MESH USE THIS
                        for faceLms in self.results.multi_face_landmarks:
                            self.drawSpec = self.mpDraw.DrawingSpec(color=(self.BLUE,self.GREEN,self.RED), thickness=1, circle_radius=1)
                            self.mpDraw.draw_landmarks(frame, faceLms, self.mpFaceConnections, self.drawSpec, self.drawSpec)
                    else:
                        self.draw_landmarks(frame, [])
                    
                    # Calculate EAR, MAR, and FAR
                    left_EAR = self.aspect_ratio(self.Left_Eye_Top_Bottom, self.Left_Eye_Left_Right, frame)
                    right_EAR = self.aspect_ratio(self.Right_Eye_Top_Bottom, self.Right_Eye_Left_Right, frame)
                    EAR = (left_EAR + right_EAR) / 2
                    MAR = self.aspect_ratio(self.Lips_Top_Bottom, self.Lips_Left_Right, frame)
                    FAR = self.aspect_ratio(self.Face_Top_Bottom, self.Face_Left_Right, frame)

                    if not self.CALIBRATE:
                        # If the Eyes are more closed than the threshold and the person is not yawning or looking away
                        if EAR < self.EYE_AR_THRESH and MAR < self.MOUTH_AR_THRESH and self.FACE_AR_THRESH_LOWER < FAR < self.FACE_AR_THRESH_UPPER:
                            self.COUNTER += 1

                            # if the eyes were closed for a sufficient number of frames then sound the alarm
                            if self.COUNTER >= self.CONSEC_FRAMES:
                                # if the alarm is not already on, turn it on
                                if not self.ALARM_ON:
                                    self.ALARM_ON = True
                                    # Play the text
                                    tts.run("Your eyes are closing")

                                # draw an alert on the frame    
                                cv2.putText(frame, "Eyes closed", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                                
                        # If the mouth is more open than the threshold (yawning)
                        elif MAR > self.MOUTH_AR_THRESH:
                            self.COUNTER += 1

                            # if this happens for sufficient number of frames
                            if self.COUNTER >= self.CONSEC_FRAMES:
                                # if alarm not already on turn it on
                                if not self.ALARM_ON:
                                    self.ALARM_ON = True
                                    # Play the text
                                    tts.run("Yawning")
                                
                                # draw an alert on the frame
                                cv2.putText(frame, "Yawning", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

                        # If the face is pointed up or down
                        elif FAR < self.FACE_AR_THRESH_LOWER:
                            self.COUNTER += 1

                            # if this happens for sufficient number of frames
                            if self.COUNTER >= self.CONSEC_FRAMES:
                                # if alarm not already on turn it on
                                if not self.ALARM_ON:
                                    self.ALARM_ON = True
                                    # Play the text
                                    tts.run("Dozing off")
                                
                                # draw an alert on the frame
                                cv2.putText(frame, "Nodding off", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

                        # If the face is pointed left or right
                        elif FAR > self.FACE_AR_THRESH_UPPER:
                            self.COUNTER += 1

                            # if this happened for a sufficient number of frames then sound the alarm
                            if self.COUNTER >= self.CONSEC_FRAMES:
                                # if the alarm is not already on, turn it on
                                if not self.ALARM_ON:
                                    self.ALARM_ON = True
                                    # Play the text
                                    tts.run("You are not paying attention")

                                # draw an alarm on the frame
                                cv2.putText(frame, "Inattentive", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

                        # otherwise, the aspect ratio is within all thresholds, so reset the counter and alarm
                        else:
                            self.COUNTER = 0
                            self.ALARM_ON = False

                    else:
                    # We are calibrating
                        print(self.CALIBRATION_COUNTER)
                        if self.CALIBRATION_COUNTER <= self.interval:
                            cv2.putText(frame, "Look straight at the camera", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                            self.Base_EAR += EAR
                        elif self.FIRST_EAR_IT:
                            self.Base_EAR = self.Base_EAR/self.interval
                            self.EYE_AR_THRESH = 0.8*self.Base_EAR
                            self.FIRST_EAR_IT = False
                            print(self.Base_EAR)

                        # Take the average of the EAR for baseline
                        if self.interval < self.CALIBRATION_COUNTER <= (2*self.interval)+50:
                            cv2.putText(frame, "Open your mouth wide", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                            # Give them some time to open the mouth
                            if self.CALIBRATION_COUNTER > self.interval+50:
                                self.Base_MAR += MAR
                        elif self.FIRST_MAR_IT:
                            self.Base_MAR = self.Base_MAR/self.interval
                            self.MOUTH_AR_THRESH = 0.8*self.Base_MAR
                            self.FIRST_MAR_IT = False
                            print(self.Base_MAR)
                        
                        if self.CALIBRATION_COUNTER > (2*self.interval)+50:
                            self.CALIBRATE = False
                            self.FIRST_EAR_IT = True
                            self.FIRST_MAR_IT = True
                            self.DONE = True


                    # draw the computed aspect ratios on the frame to help with debugigng and setting the correct
                    # aspect ratio thresholds and frame counters
                    cv2.putText(frame, "EAR: {:.2f}".format(EAR), (500,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                    cv2.putText(frame, "MAR: {:.2f}".format(MAR), (500,60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                    cv2.putText(frame, "FAR: {:.2f}".format(FAR), (500,90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

                # Convert to a format that can be displayed in Qt
                Image = cv2.cvtColor(frame, cv2.COLOR_HLS2RGB)
                ConvertToQtFormat = QImage(Image.data, Image.shape[1], Image.shape[0], QImage.Format_RGB888)
                Pic = ConvertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.ImageUpdate.emit(Pic)
        


    
    def stop(self):
        self.ThreadActive = False
        self.quit()
