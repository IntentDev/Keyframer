# various utilities module
# use module level function for standalone functions
# use classMethod() or staticmethod in classes fi class 
# is meant to be used rather than object
import re

def ExpandValue(value, to1, to2):
	# expands normalized value
	value = ((to2 - to1) * (value)) / 1.0 + to1
	return value

def NormalizeValue(value, from1, from2):
	return (value - from1) / (from2 - from1)

def RangeValue(from1, from2, to1, to2, value):
	value = ((to2 - to1) * (value -from1)) / (from2 - from1)  + to1
	return value

def getOpDepth(operator, maxSearchDepth=100):
	isRoot = False
	i = 1
	depth = 0
	while isRoot is False and i < maxSearchDepth:
		if operator.parent(i) == root:
			isRoot = True
			depth = i
		i += 1
	return(depth)

class TextportLogging:

	@staticmethod
	def printStatusMessage(message, error=False):
		if error:
			title= "ERROR"
			print(f"{title}:", message, error)
		else:
			title= "SUCCESS"	
			print(f"{title}:", message)

class VMath:
	# example (only really needed if needed access attributes between functions)	
	@classmethod
	def sum2(cls, x, y):
		return x + y

	@staticmethod
	def expandValue(value, to1, to2):
		# expands normalized value
		value = ((to2 - to1) * (value)) / 1.0 + to1
		return value

	@staticmethod
	def normalizeValue(value, from1, from2):
		return (value - from1) / (from2 - from1)

	@staticmethod
	def rangeValue(value, from1, from2, to1, to2):
		value = ((to2 - to1) * (value -from1)) / (from2 - from1)  + to1
		return value		

class Timecode():
	def __init__(self, rate=None):
		if rate == None:
			self.rate = me.time.rate
		else:
			self.rate = rate

	def getSeconds(self, hours, mins , secs, frames, rate):
		return hours * 60 * 60 + mins * 60 + secs + frames / rate

	def TimecodeToSeconds(self, timecode):
		timecode = timecode.split(':')
		hours = int(timecode[0])
		mins = int(timecode[1])
		secs = int(timecode[2][:2])
		frames = int(timecode[2][-2:])
		return self.getSeconds(hours, mins, secs, frames, self.rate)

	def SecondsToTimecode(self, Seconds):
		frac, seconds = math.modf(Seconds)
		frames = round(self.rate * frac)
		minutes = math.floor(seconds / 60)
		hours = math.floor(minutes / 60)
		minutes = minutes % 60
		seconds = int(seconds) % 60
		hours = str(hours).zfill(2)
		minutes = str(minutes).zfill(2)
		seconds = str(seconds).zfill(2)
		frames = str(frames).zfill(2)
		return f"{hours}:{minutes}:{seconds}.{frames}"

	def TimecodeToFrames(self, timecode):
		timecode = re.split(r'[:.]', timecode)
		hours = int(timecode[0])
		mins = int(timecode[1])
		secs = int(timecode[2])
		frames = int(timecode[3])
		seconds = self.getSeconds(hours, mins, secs, frames, self.rate)
		frame = int(seconds * self.rate)
		return frame

	def ExtTimecodeToFrames(self, timecode, rate):
		timecode = re.split(r'[:.]', timecode)
		hours = int(timecode[0])
		mins = int(timecode[1])
		secs = int(timecode[2])
		frames = int(timecode[3])
		seconds = self.getSeconds(hours, mins, secs, frames, rate)
		frame = int(seconds * rate)
		return frame

	def FramesToTimecode(self, frame):
		frameRate = self.rate
		ff = int(frame % frameRate)
		s = int(frame // frameRate)
		l = (s // 3600, s // 60 % 60, s % 60, ff)
		hours = str(l[0]).zfill(2)
		minutes = str(l[1]).zfill(2)
		seconds = str(l[2]).zfill(2)
		frames = str(l[3]).zfill(2)
		return f"{hours}:{minutes}:{seconds}.{frames}"

	def ExtFramesToTimecode(self, frame, rate):
		frameRate = self.rate
		ff = int(frame % rate)
		s = int(frame // rate)
		l = (s // 3600, s // 60 % 60, s % 60, ff)
		hours = str(l[0]).zfill(2)
		minutes = str(l[1]).zfill(2)
		seconds = str(l[2]).zfill(2)
		frames = str(l[3]).zfill(2)
		return f"{hours}:{minutes}:{seconds}.{frames}"

	def CheckAllChar(self, string, search = re.compile(r'[^\d:.]').search):
		return not bool(search(string.replace(' ', '')))

	def StringToTimecode(self, string, prevString):
		timecode = prevString		
		setTimecode = self.CheckAllChar(string)
		if setTimecode:		
			frameRate = self.rate
			tc = re.split(r'[:.]', string)
			i = 0
			frames = 0
			for val in reversed(tc):
				if val == '': val = 0
				val = int(val)
				if i == 0: frames += val
				elif i == 1: frames += val * frameRate
				elif i == 2: frames += val * 60 * frameRate
				elif i == 3: frames += val * 3600 * frameRate 
				i += 1
			timecode = self.FramesToTimecode(frames)
		return timecode
