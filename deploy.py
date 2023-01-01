### importing required libraries
import torch
import cv2
import time
import imutils
import numpy as np
from imutils.video import FPS
import serial
ArduinoSerial = serial.Serial('/dev/ttyACM0',9600,timeout=0.1)

def detectx (frame, model):
	frame = [frame]
	results = model(frame)
	labels, cordinates = results.xyxyn[0][:, -1], results.xyxyn[0][:, :-1]

	return labels, cordinates

def plot_boxes(results, frame, classes):
	kotak = 0, 0, 0, 0

	labels, cord = results
	n = len(labels)
	x_shape, y_shape = frame.shape[1], frame.shape[0]

	size_max = 0
	size_max_index = 0

	for i in range(n):
		size_curr = abs(cord[i][3]*y_shape - cord[i][1]*y_shape)
		if size_curr > size_max:
			size_max= size_curr
			size_max_index = i

	if n > 0:
		row = cord[size_max_index]

		w1, h1, w2, h2 = float(row[0]*x_shape), float(row[1]*y_shape), float(row[2]*x_shape), float(row[3]*y_shape)
		x1, y1, x2, y2 = int(row[0]*x_shape), int(row[1]*y_shape), int(row[2]*x_shape), int(row[3]*y_shape) ## Kordinat BBox
		
		kotak = x1, y1, x2, y2
		text_d = classes[int(labels[i])]

		cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 100, 200), 2) ## BBox
		cv2.rectangle(frame, (x1, y1-20), (x2, y1), (0, 100,200), -1) ## Label      
		cv2.putText(frame, 'Human' + f" {round(float(row[4]),2)}" + f"Size: {round(float(size_max), 2)}", (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.7,(255,255,255), 2)

	return frame, kotak

def follow(xcen, startX, endX):

	if xcen < 150:
		string = '3'
		print("Left: xcen = ",xcen)
		return string

	elif xcen > 300:
		string = '2'
		print("Right: xcen = ",xcen)
		return string

	elif startX < 100 and endX > 320:
		string = '1'
		print("Stopped Following")
		return string
		print("Object chase complete!!")

	elif xcen == 0:
		string = '1'
		print("Stopped Following")
		return string
		
	else:
		string = '0'
		print("Forward: xcen = ",xcen)
		return string

def main(vid_path=None):

	print(f"[INFO] Loading model... ")
   
	model =  torch.hub.load('yolov5', 'custom', source ='local', path='best.pt', force_reload=True) ### The repo is stored locally
	fps = FPS().start()
	classes = model.names ### class names in string format

	vid_path = '/home/fadhel/Workspace/alfiantot/1 Meter.mp4'

	if vid_path !=None:
		print(f"[INFO] Working with video: {vid_path}")

		## reading the video
		cap = cv2.VideoCapture(vid_path)
		frame_no = 1
		isStop = 0
		cv2.namedWindow("vid_out", cv2.WINDOW_NORMAL)
		while True:
			start_time = time.time()
			ret, frame = cap.read()
			if ret :
				frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
				frame = imutils.resize(frame, width=500)
				results = detectx(frame, model = model)
				frame = cv2.cvtColor(frame,cv2.COLOR_RGB2BGR)
				frame, box = plot_boxes(results, frame,classes = classes)

				box = np.array(box)
				(startX, startY, endX, endY) = box.astype("int")
				xcen = (endX + startX)/2
				#ycen = (endY + startY)/2

				string = follow(xcen, startX, endX)
				
				cv2.imshow("vid_out", frame)
				ArduinoSerial.write(bytes(string, 'utf-8'))
				PWM_Value = ArduinoSerial.readline().decode().strip()
				print(f'[INFO] PWM Value : {PWM_Value}')
				#end_time = time.time()
				#process_time = end_time - start_time
				#print("[INFO] computational time: ",process_time)

				if cv2.waitKey(1) & 0xFF == ord('q'):
					string = '1'
					isStop = 1
				if (isStop == 1 and PWM_Value == "0 + 0"):
					print('[INFO] Process Terminated')
					break

				frame_no += 1

				fps.update()

		
		print(f"[INFO] Clening up. . . ")
		fps.stop()
		print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
		print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
	
		## closing all windows
		cv2.destroyAllWindows()

### -------------------  calling the main function-------------------------------
main(vid_path=0) 
