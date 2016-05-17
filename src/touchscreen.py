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

class PointListener(Leap.Listener):
		
	def __init__(self, controller):
		super(PointListener, self).__init__()
		
		self.mouse_multiplier = 2.0
		
		# Mouse variables
		self.m = PyMouse()
		self.x, self.y = self.m.position()
		
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
		point = frame.pointables.frontmost
		if point.is_valid and point.id == self.prev_point.id:
			# If the point was present in the last frame move relative to it
			moved = point.tip_position - self.prev_point.tip_position
			self.mouse_move_rel(moved.x, -moved.y)
			print 'Point #{}: "{}" - {}'.format(point.id, 'Finger' if point.is_finger else 'Tool', moved)
			
	def mouse_move_rel(self, x, y):
		self.x += x * self.mouse_multiplier
		self.y += y * self.mouse_multiplier
		self.m.move(int(self.x), int(self.y))

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
	try:
		sys.stdin.readline()
	except KeyboardInterrupt:
		pass		

if __name__ == "__main__":
	main()
	