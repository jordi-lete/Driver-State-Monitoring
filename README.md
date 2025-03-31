# Driver-State-Monitoring
This is a driver state monitoring application capable of detecting features that might indicate inattentiveness. I consider cases where the drivers eyes begin to close or yawning as indicators that the driver is drowsy; and facial pose, indicative that the driver is looking away from the road and inattentive. However, more advance systems may also consider cases such as the use of mobile phones, smoking, talking to passengers, or drinking. Such systems may require hand and finger tracking.

I use Google's mediapipe library to extract key facial landmarks, and a methodology outlined by Soukupová and Cech (http://vision.fe.uni-lj.si/cvww2016/proceedings/papers/05.pdf) to measure eye closure. The Mediapipe models I'm using consists of two real-time deep neural network models that work together. The first accurately locates and crops face locations within the full image; this drastically reduces the computational requirement for the second network which calculates the locations of key facial landmarks and predicts the approximate 3D surface via regression.

![image](https://github.com/user-attachments/assets/05829454-bbb2-4972-9b24-7aca66902cb8)



## I. Installation and Running the Program

### 1.1 If python is already installed on your PC:

Clone the repository:
```
git clone https://github.com/jordi-lete/Driver-State-Monitoring.git
```

Inside the project directory, install requirements:
```
pip install -r requirements.txt
```

### 1.2 To run the program:
```
python scripts/mainwindow.py
```

A portable version of this code is also available (which can be run via a batch script) if python is not installed on the machine. This is large and not available on the git repo, however.
