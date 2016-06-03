import os, sys, inspect, thread, time
src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
lib_path_py = os.path.abspath(os.path.join(src_dir, '../lib/'))
arch_dir = '../lib/x64' if sys.maxsize > 2**32 else '../lib/x86'
lib_path_pyd = os.path.abspath(os.path.join(src_dir, arch_dir))
sys.path.insert(0, lib_path_py)
sys.path.insert(0, lib_path_pyd)

# --------------------------------------------------------------------------------

import Leap
from pymouse import PyMouse

import numpy as np
from numpy.linalg import inv


def deriveTransform(o1, o2, o3, o4, t1, t2, t3, t4):
	A = to3D(o1, o2, o3, o4)
	B = to3D(t1, t2, t3, t4)
	return B.dot(inv(A))

def to3D(a, b, c, d):
	A = np.vstack([np.column_stack([a, b, c]), np.array([1, 1, 1])])
	B = np.vstack([d[np.newaxis].T, 1])
	X = inv(A).dot(B)
	return A * X.T

def clamp(x, minimum, maximum):
	return min(maximum, max(minimum, x))


class PointListener(Leap.Listener):
		
	def __init__(self, controller):
		super(PointListener, self).__init__()
		
		# Calibration	
		self.top_left = None
		self.top_right = None
		self.bot_left = None
		self.bot_right = None
		self.transform = None

		# Mouse variables
		self.m = PyMouse()
		#self.x_dim, self.y_dim = m.screen_size()
		
		# Leap motion variables
		self.controller = controller 
		self.prev_point = None
		
		# Leap motion listener auto-registration
		self.controller.add_listener(self)
		
	def __del__(self):
		self.controller.remove_listener(self)
	
	def on_connect(self, controller):
		print "Connected"
		
	def on_frame(self, controller):
		frame = controller.frame()
		# If none set the initial
		self.prev_point = self.prev_point or frame.pointables.frontmost
		# update	
		self.update(frame)
		# Remember the last position
		self.prev_point = frame.pointables.frontmost

	def update(self, frame):
		# Get the front most finger or tool
		self.mouse_move(frame.pointables.frontmost)
			

	def mouse_move(self, point):
		if not point.is_valid:
			return 

		if (self.bot_left is None) or (self.bot_right is None) or (self.top_left is None) or (self.top_right is None) or (not point.is_valid):
			return

		# Compute the projective transformation
		if (self.transform is None):
			o1 = np.array([self.top_left.x, self.top_left.y])
			o2 = np.array([self.top_right.x, self.top_right.y])
			o3 = np.array([self.bot_right.x, self.bot_right.y ])
			o4 = np.array([self.bot_left.x, self.bot_left.y])

			t1 = np.array([0, 0])
			t2 = np.array([1, 0])
			t3 = np.array([1, 1])
			t4 = np.array([0, 1])

			self.transform = deriveTransform(o1, o2, o3, o4, t1, t2, t3, t4)

		# Get the stabilized position from leap motion
		pos = point.stabilized_tip_position
		print 'Point #{}: "{}" - {}'.format(point.id, 'Finger' if point.is_finger else 'Tool', pos)

		# Compute transformation
		normalized_screen = self.transform.dot(np.array([pos.x, pos.y, 1])[np.newaxis].T)

		# Homogeneous coordinates to cartesian coordinate system
		w = normalized_screen[2][0]
		x = normalized_screen[0][0] / w
		y = normalized_screen[1][0] / w
		
		x = clamp(x, 0, 1)
		y = clamp(y, 0, 1)

		self.m.move(int(x * 1920), int(y * 1080))
		
	def set_topl(self):
		if self.prev_point.is_valid:
			self.top_left = self.prev_point.stabilized_tip_position
			print "Point: {}".format(self.top_left)
		else:
			print "No point detected"

	def set_topr(self):
		if self.prev_point.is_valid:
			self.top_right = self.prev_point.stabilized_tip_position
			print "Point: {}".format(self.top_right)
		else:
			print "No point detected"

	def set_botl(self):
		if self.prev_point.is_valid:
			self.bot_left = self.prev_point.stabilized_tip_position
			print "Point: {}".format(self.bot_left)
		else:
			print "No point detected"

	def set_botr(self):
		if self.prev_point.is_valid:
			self.bot_right = self.prev_point.stabilized_tip_position
			print "Point: {}".format(self.bot_right)
		else:
			print "No point detected"

# --------------------------------------------------------------------------------

def main():
	# Create the listener and get the controller
	controller = Leap.Controller()
	# Enable background control
	controller.set_policy(Leap.Controller.POLICY_BACKGROUND_FRAMES)
	# Have the sample listener receive events from the controller
	listener = PointListener(controller)

	# Keep this process running until Enter is pressed
	print "Press Enter to quit"
	while True:
		try:
			key = sys.stdin.readline()
		except KeyboardInterrupt:
			break
		if 'tl' in key:
			listener.set_topl()
		elif 'tr' in key:
			listener.set_topr()
		elif 'bl' in key:
			listener.set_botl()
		elif 'br' in key:
			listener.set_botr()
		#else:
		#	break

if __name__ == "__main__":
	main()
	