WIDGETS = iop.Widgets
KEYFRAMER = parent.Keyframer

class WidgetVecExt(WIDGETS.Widget):
	"""
	WidgetVecExt description
	"""
	def __init__(self, ownerComp):
		super().__init__(ownerComp)	

	def SetValue(self, element, value):
		KEYFRAMER.SetSelectedFuncs[element.name](value)

	def UpdateViews(self, elementsValues):
		for key,value in elementsValues.items():
			if key != 'function':
				self.elementDict[key].UpdateView(None, value)	
			else:
				self.elementDict[key].UpdateView(value)	
			# print(key, value)	

	def UpdateView(self, element, value):
		self.elementDict[element].UpdateView(None, value)

	def UpdateViewKey(self, frame, value):
		self.elementDict['frame'].UpdateView(None, frame)
		self.elementDict['value'].UpdateView(None, value)

	def UpdateViewInHandle(self, slope, accel):
		self.elementDict['inslope'].UpdateView(None, slope)
		self.elementDict['inaccel'].UpdateView(None, accel)

	def UpdateViewOutHandle(self, slope, accel):
		self.elementDict['outslope'].UpdateView(None, slope)
		self.elementDict['outaccel'].UpdateView(None, accel)

	def UpdateViewFunction(self, value):
		self.elementDict['function'].UpdateView(value)

	def GetState(self):
		fullState = {key:e.GetState() for key,e in self.elementDict.items()
				if e in self.elementsUpdate}
		state = {}
		for key, val in fullState.items():
			if isinstance(val, dict):
				state[key] = val['Field']
			else:
				state[key] = val
		return state

	def ActiveElement(self, name, value):
		self.elementDict[name].Active(value)

	def ActiveKey(self, active):
		if active:
			self.Active(active)
		else:
			self.elementDict['frame'].Active(active)
			self.elementDict['value'].Active(active)	
			self.elementDict['function'].Active(active)			

	def ActiveInHandle(self, active):
		self.elementDict['inslope'].Active(active)
		self.elementDict['inaccel'].Active(active)

	def ActiveOutHandle(self, active):
		self.elementDict['outslope'].Active(active)
		self.elementDict['outaccel'].Active(active)

	def ActiveAll(self, key, inHandle, outHandle):
		self.ActiveKey(key)
		self.ActiveInHandle(inHandle)
		self.ActiveOutHandle(outHandle)				