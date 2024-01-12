import colorsys
import copy
vsu = op('vsu').module
from pprint import pprint
if hasattr(parent, 'Vision'):
	VSN = parent.Vision
else:
	VSN = None

WIDGETS = iop.Widgets

PI = 3.1415926535897932384626433832795
PI2 = 2 * PI


class Widget:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.parent = ownerComp.parent()
		self.name = ownerComp.name
		self.par = ownerComp.par
		self.panel = ownerComp.panel
		self.contextMenu = self.ownerComp.iop.ContextMenu
		if hasattr(ownerComp.parent, 'widgetView'):
			self.View = ownerComp.parent.widgetView
		else:
			self.View = ownerComp

		self.elements = ownerComp.findChildren(tags=['WidgetElement', 'Widget'], depth=1)
		self.elements.sort(key=lambda x: x.par.alignorder.eval())
		self.elementDict = {element.name:element for element 
															in self.elements}
		self.elementsUpdate = [element for element in self.elements
											if hasattr(element, 'UpdateView')]
		self.numElementsUpdate = len(self.elementsUpdate)
		self.contextMenuItems = [
			{'label': 'Set Default', 'func': self.SetDefault},
			{'label': 'Copy Value', 'func': self.CopyValue},
			{'label': 'Paste Value', 'func': self.PasteValue},
		]		

	def UpdateView(self, element, value):
		self.elementDict[element].UpdateView(value)
		
	def SetValue(self, element, value):
		"""Override this function in derived class if needed."""
		self.parent.SetValue(self.ownerComp, value)
		pass

	def SetupFromVar(self, var):
		# override in each extension if needed
		pass

	def SetDefault(self, *args, **kwargs):
		# override in each extension if needed
		pass

	def CopyValue(self, *args, **kwargs):
		# override in each extension if needed
		pass

	def PasteValue(self, *args, **kwargs):
		# override in each extension if needed
		pass

	def GetState(self):
		return {key:e.GetState() for key,e in self.elementDict.items()
				if e in self.elementsUpdate}

	def Active(self, active):
		for element in self.elementsUpdate:
			element.Active(active)

class WidgetVar(Widget):
	"""
	WidgetButtonExt description
	"""
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		self.label = ownerComp.op('Label')
		self.varName = self.name
		self.varAttr = 'val'

	@property
	def plugin(self):
		return self.par.Plugin.eval()

	@property
	def var(self):
		return getattr(self.plugin.Var, self.varName)

	def UpdateView(self, element, value):
		for element in self.elementsUpdate:
			element.UpdateView(value)

	def SetupFromVar(self, var):
		md = var.metadata
		if md.get('label') != None:
			self.label.par.Labeltext = md['label']
		else:	
			self.label.par.Labeltext = var.name	

	def OpenContextMenu(self, element):
		self.contextMenu.OpenMenu(self, self.contextMenuItems)

	def SetDefault(self, *args, **kwargs):
		value = self.var.metadata[self.varAttr]['default']
		VSN.SetVarAttr(self.plugin, self.varName, self.varAttr, value)
		pass

	def CopyValue(self, *args, **kwargs):
		self.contextMenu.CopiedValue = [getattr(self.var, self.varAttr)]
		pass

	def PasteValue(self, *args, **kwargs):
		prevValue = getattr(self.var, self.varAttr)
		value = self.contextMenu.CopiedValue[0]
		if isinstance(value, (int, float)):
			VSN.SetVarAttr(self.plugin, self.varName, self.varAttr, value)	
		ui.undo.startBlock('Paste Value')
		ui.undo.addCallback(self.undoPaste, [prevValue, value])
		ui.undo.endBlock()
	
	def undoPaste(self, isUndo, info):
		if isUndo:
			value = info[0]
		else:
			value = info[1]
		if isinstance(value, (int, float)):
			VSN.SetVarAttr(self.plugin, self.varName, self.varAttr, value)

class WidgetProperty:
	def __init__(self, element):
		self.element = element
	
	def __get__(self, obj, objType=None):
		return self.element
	
	def __set__(self, obj, value):
		self.element.UpdateView(value)

class Element:
	def __init__(self, ownerComp, updateElements):
		self.ownerComp = ownerComp
		self.parent = ownerComp.parent()
		self.name = ownerComp.name
		self.par = ownerComp.par
		self.panel = ownerComp.panel
		self.panelexecDat = ownerComp.op('panelexec')
		self.updateElements = updateElements

		if hasattr(ownerComp.par, 'Doundo'):
			self.doUndo = ownerComp.par.Doundo.eval()	
		else:
			for i in range(vsu.getOpDepth(ownerComp)):
				if hasattr(ownerComp.parent(i).par, 'Doundo'):
					self.doUndo = ownerComp.parent(i).par.Doundo.eval()
					break
				else:
					self.doUndo = True

	def ExpandVal(self, low, high, value, Type):
		value = ((high - low) * (value)) / 1 + low
		if Type == 'int':
			value = round(value)
		return value

	def NormalizeVal(self, low, high, value):
		return (value - low) / (high - low)

	def NormalizeValMod(self, low, high, value):
		low = -max(abs(low),abs(high))
		high = max(abs(low),abs(high))
		return (value - low) / (high - low)

	def RangeVal(self, from1, from2, to1, to2, value, Type):
		value = ((to2 - to1) * (value -from1)) / (from2 - from1)  + to1
		if Type == 'int':
			value = math.ceil(value)
		return value

	def OnRollover(self, value):
		value = max(self.panel.rollover.val, self.panel.lselect.val)
		bgCol = self.bgCols[value]
		self.par.bgcolorr = bgCol[0]
		self.par.bgcolorg = bgCol[1]
		self.par.bgcolorb = bgCol[2]
		self.par.bgalpha = bgCol[3]

	def OnRSelectOffToOn(self):
		if hasattr(self.parent, 'OpenContextMenu'):
			self.parent.OpenContextMenu(self)

	def GetColors(self, *tupletNames):
		colors = []
		for tupletName in tupletNames:
			tuplet = self.ownerComp.pars(f"{tupletName}*")
			colors.append([par.eval() for par in tuplet])
		return colors

	def GetState(self):
		return self.curState

	def Active(self, active):
		self.panelexecDat.par.active = active
		self.ownerComp.par.enable = active

	@property
	def curState(self):
		return self.ownerComp.storage.get('curState')
	@curState.setter
	def curState(self, value):
		self.ownerComp.storage['curState'] = value
		
	@property
	def prevState(self):
		return self.ownerComp.storage.get('prevState')
	@prevState.setter
	def prevState(self, value):
		self.ownerComp.storage['prevState'] = value

class WidgetSettings:
	def __init__(self):
		pass

class Label(Element):
	def __init__(self, ownerComp, updateElements=None):
		self.Text = ownerComp.op('Text')
		self.textPar = self.Text.par
		super().__init__(ownerComp, updateElements)

class SliderHorz(Element):
	def __init__(self, ownerComp, updateElements=None):	
		super().__init__(ownerComp, updateElements)
		self.bgCols = self.GetColors('Slidercolbg', 'Slidercolroll')
		self.knobCols = self.GetColors('Knobcolbg', 'Knobcolsel')
		self.Knob = ownerComp.op('Knob')
		self.knobPar = self.Knob.par
		self.detailLevel = ownerComp.fetch('detailLevel', 
			{'fine': 1.0, 'init': 1.0, 'prev': 1.0}, 
			storeDefault=True, search=False)

		self.undoBlockName = f"SliderHorz Value"
		self.ownerComp.fetch('curState', 0.0, search=False, storeDefault=True)
		self.ownerComp.fetch('prevState', self.curState, 
											search=False, storeDefault=True)
		self.prevState = self.curState

	def getValue(self, value):
		Type = self.par.Type
		range1 = self.par.Range1.eval()
		range2 = self.par.Range2.eval()
		value = self.ExpandVal(range1, range2, value, Type)
		if self.par.Clamp:
			value = min(range2, max(range1, value))
		return value

	def undo(self, isUndo, info):
		if isUndo:
			state = info[0]
		else:
			state = info[1]
		self.UpdateView(state)
		if self.updateElements:
			[element.UpdateView(state) for element in self.updateElements]
		self.parent.SetValue(self.ownerComp, state)

	def getDetailValue(self, value):
		return (self.detailLevel['prev'] 
				+ (value - self.detailLevel['init']) 
				* self.detailLevel['fine'])

	def OnLSelectOffToOn(self):
		self.detailLevel['init'] = self.panel.trueu.val
		fine = 1.0	
		if self.panel.alt.val and self.panel.ctrl.val:
			self.par.mouserel = True
			fine = .001
		elif self.panel.alt.val:
			self.par.mouserel = True
			fine = .01
		elif self.panel.ctrl.val:
			self.par.mouserel = True
			fine = .1
		self.detailLevel['fine'] = fine
		self.OnKnobSelect(1)
		self.prevState = self.curState

	def OnLSelectOnToOff(self):
		self.par.mouserel = False
		u = self.panel.trueu.val
		if self.detailLevel['fine'] != 1.0:		
			u = self.getDetailValue(u)
		self.detailLevel['prev'] = u
		self.detailLevel['fine'] = 1.0
		self.OnKnobSelect(0)
		if self.doUndo:
			ui.undo.startBlock(self.undoBlockName)
			ui.undo.addCallback(self.undo, [self.prevState, self.curState])
			ui.undo.endBlock()

	def OnKnobSelect(self, value):
		knobCol = self.knobCols[value]
		self.knobPar.bgcolorr = knobCol[0]
		self.knobPar.bgcolorg = knobCol[1]
		self.knobPar.bgcolorb = knobCol[2]
		self.knobPar.bgalpha = knobCol[3]
	
	def OnTrueu(self, u):
		if self.detailLevel['fine'] != 1.0:		
			u = self.getDetailValue(u)
		self.UpdateView(u, normalize=False)
		value = self.getValue(u)
		self.curState = value
		if self.updateElements:
			[element.UpdateView(value) for element in self.updateElements]
		self.parent.SetValue(self.ownerComp, value)
		
	def UpdateView(self, value, normalize=True):
		if normalize:
			self.curState = value
			range1 = self.par.Range1
			range2 = self.par.Range2
			value = self.ownerComp.NormalizeVal(range1, range2, value)
			self.detailLevel['prev'] = value
		knobWidth = self.Knob.par.w
		parentWidth = self.ownerComp.width
		self.Knob.par.x = max(min(value * parentWidth - knobWidth * .5, 
			parentWidth - knobWidth - 1), 1,)

class Field(Element):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.bgCols = self.GetColors('Fieldcolbg', 'Fieldcolroll')
		self.fontCols = self.GetColors('Fontcolcolor', 'Fontcolroll',
										'Fontcolinv', 'Fontcolbg')
		self.Text = ownerComp.op('Text')
		self.textPar = self.Text.par
		self.string = ownerComp.op('string')
		self.undoBlockName = "Field Value"
		self.ownerComp.fetch('curState', self.panel.field.val, 
											search=False, storeDefault=True)
		self.ownerComp.fetch('prevState', self.curState, 
											search=False, storeDefault=True)
		self.prevState = self.curState
		
	def OnRollover(self, value):
		self.bgCol = self.bgCols[value]
		self.par.bgcolorr = self.bgCol[0]
		self.par.bgcolorg = self.bgCol[1]
		self.par.bgcolorb = self.bgCol[2]
		self.par.bgalpha = self.bgCol[3]

		self.fontCol = self.fontCols[value]
		self.textPar.fontcolorr = self.fontCol[0]
		self.textPar.fontcolorg = self.fontCol[1]
		self.textPar.fontcolorb = self.fontCol[2]
		self.textPar.fontalpha = self.fontCol[3]

	def undo(self, isUndo, info):
		# print(info)
		if isUndo:
			state = info[0]
		else:
			state = info[1]
		self.setField(state)
		self.textPar.text = state
		
	def OnFocusOffToOn(self):
		pass

	def OnFocusOnToOff(self):
		if self.prevState != self.panel.field.val:
			value = self.panel.field.val
			self.setField(value)

	# in field undo is extremely buggy, need to create simple case
	# and report bug. 
	def OnCharacter(self, value):
		# if value != 0:
		# 	self.prevState = self.curState
		# else:	
		# 	print(self.prevState, self.panel.fieldediting.val)
		# 	self.curState = self.panel.fieldediting.val
		# 	ui.undo.startBlock(self.undoBlockName)
		# 	ui.undo.addCallback(self.undo,[self.prevState, self.curState])
		# 	ui.undo.endBlock()
		pass
			
	def setField(self, value):
		if self.par.fieldtype.eval() != 'string':
			value = float(value)
			if self.par.Clamp:
				range1 = self.par.Range1.eval()
				range2 = self.par.Range2.eval()
				value = min(range2, max(range1, value))
				self.UpdateView(value)
		self.curState = value
		if self.updateElements:
			[element.UpdateView(value) for element 
				in self.updateElements]		
		self.parent.SetValue(self.ownerComp, value)
		if self.doUndo:
			ui.undo.startBlock(self.undoBlockName)
			ui.undo.addCallback(self.undo, [self.prevState, value])
			ui.undo.endBlock()
			self.prevState = self.curState


	def UpdateView(self, value):
		if self.ownerComp.par.enable.eval():
			self.curState = value
			if self.par.fieldtype.eval() != 'string':
				self.textPar.text = f"{round(value, 5 - len(str(round(value))))}"
			else:
				self.textPar.text = value

	def OnRSelectOffToOn(self):
		self.panel.focus = False
		super().OnRSelectOffToOn()

	def OnMSelectOffToOn(self):
		self.panel.focus = False

	def OnMSelectOnToOff(self):
		self.panel.focus = False

	def Active(self, active):
		self.ownerComp.par.enable = active
		self.panelexecDat.par.active = active
		if not active:
			self.Text.par.field = ''
			self.Text.cook(force=True)
			self.Text.par.text = '' 

		else:
			self.Text.par.field = '..'
			self.Text.cook(force=True)

class Button(Element):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.btnCols = self.GetColors('Buttoncolcolor', 'Buttoncolroll',
										'Buttoncolsel', 'Buttoncolon')
		self.TextOff = ownerComp.op('TextOff')
		self.TextOn = ownerComp.op('TextOn')
		self.digits = self.ownerComp.digits
		self.toggleUndoBlockName = "Button Toggle Value"
		self.pulseUndoBlockName = "Button Pulse"
		self.ownerComp.fetch('curState', 0, 
											search=False, storeDefault=True)
		self.ownerComp.fetch('prevState', self.curState, 
											search=False, storeDefault=True)
		self.prevState = self.curState
		self.UndoCallback = None

	def undo(self, isUndo, info):
		if isUndo:
			state = info[0]
		else:
			state = info[1]
		self.UpdateView(state)
		self.parent.SetValue(self.ownerComp, state)

	def setColor(self):
		index = min(3, 
			(self.panel.rollover + self.panel.state * 2) + self.panel.lselect)
		col = self.btnCols[index]
		self.par.bgcolorr = col[0]
		self.par.bgcolorg = col[1]
		self.par.bgcolorb = col[2]
		self.par.bgalpha = col[3]

	def OnRollOffToOn(self, value):
		self.setColor()

	def OnRollOnToOff(self, value):
		self.setColor()

	def OnLSelectOffToOn(self):
		self.prevState = self.curState
		self.curState = bool(self.panel.state.val)
		self.setColor()
		self.parent.SetValue(self.ownerComp, self.curState)

	def OnLSelectOnToOff(self):
		self.setColor()
		buttonType = self.par.Buttontype.eval()
		if buttonType == 'momentary':
			self.curState = bool(self.panel.state.val)
			self.parent.SetValue(self.ownerComp, self.curState)
		if self.par.Doundo:
			if buttonType == 'toggledown':
				ui.undo.startBlock(self.toggleUndoBlockName)
				ui.undo.addCallback(self.undo, [self.prevState, self.curState])
				ui.undo.endBlock()
			elif self.UndoCallback != None:
				ui.undo.startBlock(self.pulseUndoBlockName)
				ui.undo.addCallback(self.UndoCallback, self.ownerComp)
				ui.undo.endBlock()				
			
	def UpdateView(self, value):
		if self.par.Buttontype.eval() != 'pulse':
			self.curState = value
			self.panel.state = value
			self.setColor()

	def Active(self, active):
		if not active and self.panel.state.val != 2:
			self.panel.state.val = 2
		self.ownerComp.par.enable = active
		self.panelexecDat.par.active = active
		if active:
			self.panel.state.val = 0
		
class SliderVert(Element):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.bgCols = self.GetColors('Slidercolbg', 'Slidercolroll')
		self.knobCols = self.GetColors('Knobcolbg', 'Knobcolsel')		
		self.Knob = ownerComp.op('Knob')
		self.knobPar = self.Knob.par
		self.panelexecAutoDat = ownerComp.op('panelexecAuto')
		self.keyboard = self.ownerComp.iop.MasterKeyboard
		self.ctrl = self.keyboard['kctrl']
		self.alt = self.keyboard['kalt']
		self.detailLevel = ownerComp.fetch('detailLevel', 
			{'fine': 1.0, 'init': 1.0, 'prev': 1.0}, 
			storeDefault=True, search=False,)

		self.undoBlockName = f"SliderVert Value"
		self.ownerComp.fetch('curState', 0.0, search=False, storeDefault=True)
		self.ownerComp.fetch('prevState', self.curState, 
											search=False, storeDefault=True)
		self.prevState = self.curState

	def getValue(self, value):
		Type = self.par.Type
		range1 = self.par.Range1.eval()
		range2 = self.par.Range2.eval()
		value = self.ExpandVal(range1, range2, value, Type)
		if self.par.Clamp:
			value = min(range2, max(range1, value))
		return value

	def undo(self, isUndo, info):
		if isUndo:
			state = info[0]
		else:
			state = info[1]
		if self.par.Slidermode != 'AUTO':
			self.UpdateView(state)
		if self.updateElements:
			[element.UpdateView(state) for element in self.updateElements]
		self.parent.SetValue(self.ownerComp, state)

	def OnRollover(self, value):
		value = max(self.panel.rollover.val, self.panel.lselect.val)
		bgCol = self.bgCols[value]
		self.par.bgcolorr = bgCol[0]
		self.par.bgcolorg = bgCol[1]
		self.par.bgcolorb = bgCol[2]
		self.par.bgalpha = bgCol[3]
		if self.updateElements:
			self.updateElements[0].panel.rollover = value	

	def getDetailValue(self, value):
		return (self.detailLevel['prev'] 
				+ (value - self.detailLevel['init']) 
				* self.detailLevel['fine'])

	def setFine(self):
		value = self.getFine()
		if value != 1.0:
			self.par.mouserel = True
		self.detailLevel['fine'] = value
	
	def getFine(self):
		fine = 1.0
		if self.alt and self.ctrl:
			fine = .001
		elif self.alt:
			fine = .01
		elif self.ctrl:
			fine = .1
		return fine
	
	def OnKnobSelect(self, value):
		knobCol = self.knobCols[value]
		self.knobPar.bgcolorr = knobCol[0]
		self.knobPar.bgcolorg = knobCol[1]
		self.knobPar.bgcolorb = knobCol[2]
		self.knobPar.bgalpha = knobCol[3]

	def OnLSelectOffToOn(self):
		if self.par.Slidermode == 'REL':
			self.par.mouserel = True
			self.detailLevel['init'] = self.panel.truev * self.par.Relposscale
		elif self.par.Slidermode == 'AUTO':
			self.UpdateKnob(.5)
			self.par.mouserel = True
			self.detailLevel['init'] = self.panel.truev.val						
		else:
			self.detailLevel['init'] = self.panel.truev.val
		self.setFine()
		self.OnKnobSelect(1)
		self.prevState = self.curState
	
	def OnLSelectOnToOff(self):
		self.panel.ctrl = 0
		self.panel.alt = 0
		self.par.mouserel = False
		if self.detailLevel['fine'] != 1.0 or self.par.Slidermode != 'ABS':
			value = self.panel.truev.val * self.par.Relposscale		
			value = self.getDetailValue(value)
		elif self.par.Slidermode == 'ABS':
			value = 0.0
		else:
			value = self.panel.truev.val
		if self.par.Clamp:
			value = min(1, max(0, value))

		self.detailLevel['fine'] = 1.0
		if self.par.Slidermode == 'AUTO':
			self.UpdateKnob(.5)
		else:
			self.detailLevel['prev'] = value
		self.OnKnobSelect(0)
		if self.doUndo:
			ui.undo.startBlock(self.undoBlockName)
			ui.undo.addCallback(self.undo, [self.prevState, self.curState])
			ui.undo.endBlock()

	def OnTruev(self, v):
		if self.par.Slidermode != 'AUTO':
			if self.detailLevel['fine'] != 1.0 or self.par.Slidermode != 'ABS':
				v *= self.par.Relposscale		
				v = self.getDetailValue(v)
			self.UpdateView(v, normalize=False)
			value = self.getValue(v)
			self.curState = value
		if self.updateElements:
			[element.UpdateView(value) for element in self.updateElements]
		self.parent.SetValue(self.ownerComp, value)

	def OnWhileOn(self):
		range1 = self.par.Range1.eval()
		range2 = self.par.Range2.eval()
		Type = self.par.Type
		fine = self.getFine()
		v = self.panel.truev.val - self.detailLevel['init']
		v *= self.par.Relposscale * fine * .1 * self.par.Autospeed
		self.UpdateKnob(v * 10 / self.par.Autospeed + .5)
		v = v + self.detailLevel['prev']
		if self.par.Clamp:
			v = min(1, max(0, v))
		if v != self.detailLevel['prev']:
			self.detailLevel['prev'] = v
			value = self.ExpandVal(range1, range2, v, Type)
			if self.updateElements:
				[element.UpdateView(value) for element in self.updateElements]
			self.parent.SetValue(self.ownerComp, value)

			self.curState = value
	
	def UpdateView(self, value, normalize=True):	
		if normalize:
			self.curState = value
			range1 = self.par.Range1
			range2 = self.par.Range2
			value = self.ownerComp.NormalizeVal(range1, range2, value)
			self.detailLevel['prev'] = value
		if self.par.Slidermode != 'AUTO':
			self.UpdateKnob(value)

	def UpdateKnob(self, value):
		knobHeight = self.Knob.height
		ownerHeight = self.ownerComp.height
		self.Knob.par.y = max(min(value * ownerHeight - knobHeight * .5, 
			ownerHeight - knobHeight - 2), 2,)

	def Active(self, active):
		self.ownerComp.par.enable = active
		self.panelexecDat.par.active = active
		self.panelexecAutoDat.par.whileon = active
		self.Knob.par.display = active

class Droplist(Element):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.DroplistListView = self.ownerComp.iop.DroplistListView
		self.ListItems = ownerComp.op('ListItems')
		self.button = ownerComp.op('Button')
		self.ItemHeight = self.button.par.h
		self.undoBlockName = "Droplist Value"
		self.ownerComp.fetch('curState', 0, 
											search=False, storeDefault=True)
		self.ownerComp.fetch('prevState', self.curState, 
											search=False, storeDefault=True)
		self.prevState = self.curState

	@property
	def ListWidth(self):
		return self.button.width

	def undo(self, isUndo, info):
		if isUndo:
			state = info[0]
		else:
			state = info[1]
		self.UpdateView(state)
		self.parent.SetValue(self.ownerComp, state)

	def OnSelectItem(self, itemIndex):
		self.prevState = self.curState
		self.UpdateView(itemIndex)
		self.parent.SetValue(self.ownerComp, itemIndex)
		if self.doUndo:
			ui.undo.startBlock(self.undoBlockName)
			ui.undo.addCallback(self.undo, [self.prevState, self.curState])
			ui.undo.endBlock()

	def UpdateListItems(self, items):
		# TODO implement...
		pass

	def UpdateView(self, itemIndex):
		self.curState = itemIndex
		buttonLabel = self.ListItems[itemIndex, 0].val
		self.button.par.Offtext = buttonLabel
		self.button.par.Ontext = buttonLabel

	def SetValue(self, element, value):
		self.DroplistListView.OpenList(self.ownerComp)

	def Active(self, active):
		self.button.Active(active)

class DroplistListView(Element):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.droplist = self.ownerComp.op('dropContainer/list')
		self.selectListItems = ownerComp.op('selectListItems')
		self.window = self.ownerComp.op('window')
		self.listContainer = self.ownerComp.op('listContainer')
		self.list = self.listContainer.op('list')
		self.absMouse = ownerComp.par.Absolutemousechop.eval()

		self.DroplistWidget = None
		self.listItems = ownerComp.op('listItems')
		pass

	def OnLSelectOnToOff(self):
		itemIndex = int(self.list.panel.celloverid)
		if itemIndex != -1:
			self.DroplistWidget.OnSelectItem(itemIndex)
			self.window.par.winclose.pulse()

	def OpenList(self, droplistWidget):
		self.DroplistWidget = droplistWidget	
		self.listItems = self.DroplistWidget.ListItems
		opened = self.window.isOpen
		self.selectListItems.par.dat = self.listItems

		maxHeight = int(self.DroplistWidget.par.Maxlistheight)
		compH = self.listItems.numRows * self.DroplistWidget.ItemHeight
		height = min(maxHeight, compH)
		width = self.DroplistWidget.ListWidth
		self.listContainer.par.w = width
		if self.listContainer.par.pvscrollbar:
			w2 = width - 12
			self.list.par.w = w2
		else:
			self.list.par.w = width
		self.listContainer.par.h = height

		if opened == False:
			absMouseY = self.absMouse['ty'].eval()
			mouseX = (self.DroplistWidget.panel.insideu 
						* self.DroplistWidget.width)
			mouseY = (self.DroplistWidget.panel.insidev 
						* self.DroplistWidget.height)

			x =  width - mouseX - 8
			if absMouseY >= height + self.DroplistWidget.ItemHeight:
				y = - height * 0.5 - mouseY
			else:
				y = height * 0.5 + (self.DroplistWidget.par.h - mouseY)

			self.window.par.winoffsetx = x
			self.window.par.winoffsety = y
			self.window.par.winopen.pulse()
			self.listContainer.setFocus()
		else:
			self.window.par.winclose.pulse()

class MultiButton(Element):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.cellAttribs = ownerComp.cellAttribs
		self.CurItem = ownerComp.fetch('CurrentItem', [None, None, None], 
			search=False, storeDefault=True)
		self.PrevItem = ownerComp.fetch('PrevItem', [None, None, None], 
			search=False, storeDefault=True)
		self.parexec = self.ownerComp.op('parexec')
		self.getSettings()
		self.GetToggles()
		self.ownerComp.par.reset.pulse()
		self.undoBlockName = "RadioButton Value"
		self.ownerComp.fetch('curState', self.CurItem[2], 
											search=False, storeDefault=True)
		self.ownerComp.fetch('prevState', self.curState, 
											search=False, storeDefault=True)
		self.prevState = self.curState
		self.lselect = False
		self.rselect = False		
		self.mselect = False

		self.textJustifyModes = [JustifyType.TOPLEFT, JustifyType.TOPCENTER,
								JustifyType.TOPRIGHT, JustifyType.CENTERLEFT,
								JustifyType.CENTER, JustifyType.CENTERRIGHT,
								JustifyType.BOTTOMLEFT, JustifyType.BOTTOMCENTER,
								JustifyType.BOTTOMRIGHT]

	@property
	def Toggles(self):
		return self.ownerComp.storage.get('Toggles', [[]])
	@Toggles.setter
	def Toggles(self, value):
		self.ownerComp.storage['Toggles'] = value

	def undo(self, isUndo, info):
		if isUndo:
			state = info[0]
		else:
			state = info[1]
		if self.Settings.Type != 'toggledown':
			self.UpdateView(state)
		else:
			self.Toggles[state[0]][state[1]] = state[2]
			cell = state[0] * self.Settings.cols + state[1]
			self.UpdateView(cell)
		self.SetValue(state)

	def getSettings(self):
		self.Settings = WidgetSettings()
		parNames = self.parexec.par.pars.eval().replace(',', ' ')
		parNames = parNames.split()

		for name in parNames:
			pars = self.ownerComp.pars(name)
			lenPars = len(pars)
			if lenPars > 1:
				value = [par.eval() for par in pars]
				setattr(self.Settings, name.replace('*', ''), value)
			elif lenPars == 1:
				value = pars[0].eval()
				setattr(self.Settings, name, value)
		
	def GetToggles(self, init=False):
		prevToggles = self.ownerComp.storage.get('Toggles', [[]])
		default = []
		numRows = self.Settings.rows
		numCols = self.Settings.cols
		for i in range(numRows):
			row = []
			for n in range(numCols):
				if i < len(prevToggles):
					if n < len(prevToggles[i]):
						row.append(prevToggles[i][n])
					else:
						row.append(self.ownerComp.par.Defaulttogglevalue.eval())	
				else:
					row.append(self.ownerComp.par.Defaulttogglevalue.eval())
			default.append(row)

		if not init and numRows != len(self.Toggles):
			init = True
		elif not init and len(self.Toggles) > 0:
			if numCols != len(self.Toggles[0]):
				init = True					
		if init:
			self.Toggles = default

	def OnInitCell(self, row, col, attribs):
		numCells = self.Settings.rows * self.Settings.cols
		if isinstance(self.Settings.Labels, list):
			userLabels = self.Settings.Labels
		elif isinstance(self.Settings.Labels, str):
			userLabels = self.Settings.Labels.replace(',', ' ').replace('[', ' ').replace(']', ' ')
			userLabels = userLabels.split()
		else:
			userLabels = []
		lenUserLabels = len(userLabels)
		indexLabels = [str(i) for i in range (lenUserLabels,
												lenUserLabels + numCells)]
		cell = row * self.Settings.cols + col
		source = userLabels + indexLabels
		if cell < len(source):
			cellContent = source[cell]
			attribs.text = cellContent
			attribs.textColor = self.Settings.Textcolor
			attribs.textJustify = getattr(JustifyType, 
											self.Settings.Textjustify)
			attribs.textOffsetX = self.Settings.Textoffset[0]
			attribs.textOffsetY = self.Settings.Textoffset[1]
			attribs.fontSizeX = self.par.Fontsize
			attribs.fontFace = 'Verdana'
			# attribs.fontFace = "../vlib/widgets/fonts/Inter-3.13/"\
			# 					"Inter Desktop/Inter-Regular.otf"

			if self.Settings.Type != 'toggledown':
				isSelected = int(self.CurItem[2] == cell)
				attribs.bgColor = [self.Settings.Cellcolor, 
					self.Settings.Cellselectcolor][isSelected]	
			else:
				if row < len(self.Toggles):
					if col < len(self.Toggles[row]):
						toggle = int(self.Toggles[row][col])
					else:
						toggle = 0
				else:
					toggle = 0

				attribs.bgColor = [
					self.Settings.Cellcolor, 
					self.Settings.Cellselectcolor
				][toggle]	

	def OnSelect(self, startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end):
		# print('start', self.panel.mselect.val, startrow, endrow, start, end)			
		lselect = self.panel.lselect.val
		if self.panel.lselect.val:
			if start:
				self.lselect = True
			self.OnLSelect(startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end)
		elif self.panel.rselect.val:
			if start:
				self.rselect = True
			self.OnRSelect(startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end)	
		elif self.panel.mselect.val:
			if start:
				self.mselect = True	
			self.OnMSelect(startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end)	

		if end:
			if self.lselect:
				self.OnLSelect(startrow, startcol, startcoords, 
						endrow, endcol, endcoords, start, end)
				self.lselect = False
			elif self.rselect:
				self.OnRSelect(startrow, startcol, startcoords, 
						endrow, endcol, endcoords, start, end)	
				self.rselect = False
			elif self.mselect:		
				self.OnMSelect(startrow, startcol, startcoords, 
						endrow, endcol, endcoords, start, end)	
				self.mselect = False

	def OnLSelect(self, startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end):			
		cell = startrow * self.Settings.cols + startcol
		if endrow != None and endcol != None and startrow != -1 and endrow != -1:
			endCell = endrow * self.Settings.cols + endcol
			
			lselect = self.panel.lselect.val
			if start and lselect:
				self.lselect = True
				
			if self.Settings.Type == 'radio':
				if start and self.lselect:
					self.prevState = self.curState
					self.UpdateView(cell)
					self.SetValue(cell)
				elif self.CurItem[2] != endCell and self.lselect:
					self.PrevItem[0:4] = self.CurItem
					prevItemAttribs = self.cellAttribs[self.PrevItem[0], 
						self.PrevItem[1]]
					cellAttribs = self.cellAttribs[endrow, endcol]
					cellAttribs.bgColor = self.Settings.Cellselectcolor
					if prevItemAttribs: 
							prevItemAttribs.bgColor = self.Settings.Cellcolor
					self.CurItem[0:4] = [endrow, endcol, endCell]	
					self.SetValue(endCell)
					self.curState = endCell

			elif self.Settings.Type == 'exclusive':
				if start and self.lselect:
					self.prevState = self.curState
					if cell == self.CurItem[2]:
						cell = -1 	
					self.UpdateView(cell)
					self.SetValue(cell)
				elif self.CurItem[2] != endCell and self.lselect:
					if not end:
						self.PrevItem[0:4] = self.CurItem
						prevItemAttribs = self.cellAttribs[self.PrevItem[0], 
							self.PrevItem[1]]
						cellAttribs = self.cellAttribs[endrow, endcol]
						cellAttribs.bgColor = self.Settings.Cellselectcolor
						if prevItemAttribs: 
								prevItemAttribs.bgColor = self.Settings.Cellcolor
						self.CurItem[0:4] = [endrow, endcol, endCell]	
						self.SetValue(endCell)
						self.curState = endCell

			elif self.Settings.Type == 'toggledown':
				if start and self.lselect:
					state = self.Toggles[startrow][startcol]
					self.prevState = [startrow, startcol, state]
					state = not state
					self.Toggles[startrow][startcol] = state		 
					self.UpdateView(cell)
					value = [startrow, startcol, state]
					self.SetValue(value)
					self.curState = value
					if self.doUndo:
						ui.undo.startBlock(self.undoBlockName)
						ui.undo.addCallback(self.undo, 
												[self.prevState, self.curState])
						ui.undo.endBlock()
				
				elif self.CurItem[2] != endCell and self.lselect:
					self.PrevItem[0:4] = self.CurItem
					state = self.Toggles[endrow][endcol]
					self.prevState = [endrow, endcol, state]
					state = not state
					self.Toggles[endrow][endcol] = state
					self.UpdateView(endCell)
					value = [endrow, endcol, state]
					self.SetValue(value)
					self.curState = value
					self.CurItem[0:4] = [endrow, endcol, endCell]	
					if self.doUndo:
						ui.undo.startBlock(self.undoBlockName)
						ui.undo.addCallback(self.undo, 
												[self.prevState, self.curState])
						ui.undo.endBlock()
				
			else:
				if start and self.lselect:
					self.prevState = self.curState
					self.UpdateView(cell)
					self.SetValue([cell, True])
					self.momentaryCell = cell
				elif self.CurItem[2] != endCell and self.lselect:
					self.PrevItem[0:4] = self.CurItem
					prevItemAttribs = self.cellAttribs[self.PrevItem[0], 
						self.PrevItem[1]]
					cellAttribs = self.cellAttribs[endrow, endcol]
					cellAttribs.bgColor = self.Settings.Cellselectcolor
					if prevItemAttribs: 
							prevItemAttribs.bgColor = self.Settings.Cellcolor
					self.CurItem[0:4] = [endrow, endcol, endCell]
					self.momentaryCell = endCell	
					self.SetValue([self.momentaryCell, True])
					if self.Settings.Type == 'momentary':
						self.SetValue([self.PrevItem[2], False])
				elif end and self.lselect:
					cell = -1 	
					self.UpdateView(cell)
					if self.Settings.Type == 'momentary':
						self.SetValue([self.momentaryCell, False])

			if self.doUndo and end and self.lselect and self.Settings.Type \
								not in ['pulse', 'momentary', 'toggledown']:
				ui.undo.startBlock(self.undoBlockName)
				ui.undo.addCallback(self.undo, [self.prevState, self.curState])
				ui.undo.endBlock()
				self.lselect = False
		
		elif end and self.Settings.Type in ['pulse', 'momentary']:
			cell = -1 	
			self.UpdateView(cell)
			if self.Settings.Type == 'momentary':
				self.SetValue([self.momentaryCell, False])		

		return

	def OnRSelect(self, startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end):	
		if hasattr(self.ownerComp.parent(), 'OnRSelectOffToOn') and start:
			self.ownerComp.parent().OnRSelectOffToOn(
				startrow, startcol, startcoords, 
				endrow, endcol, endcoords, start, end)
		elif hasattr(self.ownerComp.parent(), 'OnRSelectOnToOff') and end:
			self.ownerComp.parent().OnRSelectOnToOff(
				startrow, startcol, startcoords, 
				endrow, endcol, endcoords, start, end)				

	def OnMSelect(self, startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end):	
		if hasattr(self.ownerComp.parent(), 'OnMSelectOffToOn') and start:
			self.ownerComp.parent().OnMSelectOffToOn(
				startrow, startcol, startcoords, 
				endrow, endcol, endcoords, start, end)
		elif hasattr(self.ownerComp.parent(), 'OnMSelectOnToOff') and end:
			self.ownerComp.parent().OnMSelectOnToOff(
				startrow, startcol, startcoords, 
				endrow, endcol, endcoords, start, end)
		if start:
			self.prevrow = None
			self.prevcol = None
		self.row = endrow
		self.col = endcol

		if self.prevrow != None and self.prevcol != None:
			prevCell = self.prevrow * self.Settings.cols + self.prevcol
		else:
			prevCell = None
		if self.row != None and self.col != None:
			cell = self.row * self.Settings.cols + self.col
		else:
			cell = None

		if self.row != self.prevrow or self.col != self.prevcol:
			if cell != None and cell >= 0:
				if self.Settings.Type != 'toggledown':
					state = int(cell == self.CurItem[2])
				else:
					state = int(self.Toggles[self.row][self.col])
				if 	self.cellAttribs[self.row, self.col]: 
					cellAttribs = self.cellAttribs[self.row, self.col]
					cellAttribs.bgColor = [self.Settings.Cellrollcolor, 
						self.Settings.Cellrollselectcolor][state]

			if prevCell != None and prevCell >= 0:
				if self.Settings.Type != 'toggledown':
					state = int(prevCell == self.CurItem[2])
				else:
					state = int(self.Toggles[self.prevrow][self.prevcol])		
				if self.cellAttribs[self.prevrow, self.prevcol]: 
					cellAttribs = self.cellAttribs[self.prevrow, self.prevcol]
					cellAttribs.bgColor = [self.Settings.Cellcolor, 
						self.Settings.Cellselectcolor][state]
		self.prevrow = self.row
		self.prevcol = self.col

	def OnRollover(self, row, col, coords, prevrow, prevcol, prevcoords):
		# print(row, col, coords, prevrow, prevcol, prevcoords)
		if prevrow != None and prevcol != None:
			prevCell = prevrow * self.Settings.cols + prevcol
		else:
			prevCell = None
		if row != None and col != None:
			cell = row * self.Settings.cols + col
		else:
			cell = None

		if row != prevrow or col != prevcol:
			if cell != None and cell >= 0:
				if self.Settings.Type != 'toggledown':
					state = int(cell == self.CurItem[2])
				else:
					state = int(self.Toggles[row][col])
				if 	self.cellAttribs[row, col]: 
					cellAttribs = self.cellAttribs[row, col]
					cellAttribs.bgColor = [self.Settings.Cellrollcolor, 
						self.Settings.Cellrollselectcolor][state]

			if prevCell != None and prevCell >= 0 and len(self.Toggles) > 0:
				if self.Settings.Type != 'toggledown':
					state = int(prevCell == self.CurItem[2])
				else:
					state = int(self.Toggles[prevrow][prevcol])		
				if self.cellAttribs[prevrow, prevcol]: 
					cellAttribs = self.cellAttribs[prevrow, prevcol]
					cellAttribs.bgColor = [self.Settings.Cellcolor, 
						self.Settings.Cellselectcolor][state]	

	def StartEditCell(self, row, col):
		self.ownerComp.setKeyboardFocus(row, col)

	def OnEditCell(self, row, col, value):
		if hasattr(self.ownerComp.parent(), 'OnEditCell'):
			self.ownerComp.parent().OnEditCell(row, col, value)

	def UpdateView(self, value):
		self.curState = value
		if self.Settings.Type != 'toggledown':
			self.PrevItem[0:4] = self.CurItem
			if self.PrevItem[0] != None and self.PrevItem[1] != None:
				prevItemAttribs = self.ownerComp.cellAttribs[self.PrevItem[0], 
															self.PrevItem[1]]
				if prevItemAttribs:
					prevItemAttribs.bgColor = self.ownerComp.pars('Cellcolor*')		
		
		numCols = self.ownerComp.par.cols.eval()
		col = value % numCols
		row = int((value - col) / numCols)
		cellAttribs = self.ownerComp.cellAttribs[row, col]
		if cellAttribs:
			if self.Settings.Type != 'toggledown':
				cellAttribs.bgColor = self.ownerComp.pars('Cellselectcolor*')
			else:
				state = self.Toggles[row][col]	
				cellAttribs.bgColor = [self.Settings.Cellcolor, 
									self.Settings.Cellselectcolor][int(state)]
		self.CurItem[0:4] = [row, col, value]

	def SetValue(self, value):
		self.parent.SetValue(self.ownerComp, value)
		pass

class List(Element):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.cellAttribs = ownerComp.cellAttribs
		self.CurItem = ownerComp.fetch('CurrentItem', [None, None, None], 
			search=False, storeDefault=True)
		self.PrevItem = ownerComp.fetch('PrevItem', [None, None, None], 
			search=False, storeDefault=True)
		self.parexec = self.ownerComp.op('parexec')
		self.getSettings()
		self.GetToggles()
		self.ownerComp.par.reset.pulse()
		self.undoBlockName = "RadioButton Value"
		self.ownerComp.fetch('curState', self.CurItem[2], 
											search=False, storeDefault=True)
		self.ownerComp.fetch('prevState', self.curState, 
											search=False, storeDefault=True)
		self.prevState = self.curState
		self.lselect = False
		self.rselect = False		
		self.mselect = False

		self.textJustifyModes = [JustifyType.TOPLEFT, JustifyType.TOPCENTER,
								JustifyType.TOPRIGHT, JustifyType.CENTERLEFT,
								JustifyType.CENTER, JustifyType.CENTERRIGHT,
								JustifyType.BOTTOMLEFT, JustifyType.BOTTOMCENTER,
								JustifyType.BOTTOMRIGHT]

	@property
	def ListData(self):
		return self.ownerComp.storage.get('ListData', [[]])
	@ListData.setter
	def ListData(self, value):
		self.ownerComp.storage['ListData'] = value	

	@property
	def Toggles(self):
		return self.ownerComp.storage.get('Toggles', [[]])
	@Toggles.setter
	def Toggles(self, value):
		self.ownerComp.storage['Toggles'] = value


	def undo(self, isUndo, info):
		if isUndo:
			state = info[0]
		else:
			state = info[1]
		if self.Settings.Type != 'toggledown':
			self.UpdateView(state)
		else:
			self.Toggles[state[0]][state[1]] = state[2]
			cell = state[0] * self.Settings.cols + state[1]
			self.UpdateView(cell)
		self.SetValue(state)

	def getSettings(self):
		self.Settings = WidgetSettings()
		parNames = self.parexec.par.pars.eval().replace(',', ' ')
		parNames = parNames.split()

		for name in parNames:
			pars = self.ownerComp.pars(name)
			lenPars = len(pars)
			if lenPars > 1:
				value = [par.eval() for par in pars]
				setattr(self.Settings, name.replace('*', ''), value)
			elif lenPars == 1:
				value = pars[0].eval()
				setattr(self.Settings, name, value)
		
	def GetToggles(self, init=False):
		prevToggles = self.ownerComp.storage.get('Toggles', [[]])
		default = []
		numRows = self.Settings.rows
		numCols = self.Settings.cols
		for i in range(numCols):
			col = []
			for n in range(numRows):
				if i < len(prevToggles):
					if n < len(prevToggles[i]):
						col.append(prevToggles[i][n])
					else:
						col.append(self.ownerComp.par.Defaulttogglevalue.eval())	
				else:
					col.append(self.ownerComp.par.Defaulttogglevalue.eval())
			default.append(col)

		if not init and numRows != len(self.Toggles):
			init = True
		elif not init and len(self.Toggles) > 0:
			if numRows != len(self.Toggles[0]):
				init = True					
		if init:
			self.Toggles = default

	def OnInitCell(self, row, col, attribs):
		numCells = self.Settings.rows * self.Settings.cols
		if isinstance(self.Settings.Labels, list):
			userLabels = self.Settings.Labels
		elif isinstance(self.Settings.Labels, str):
			userLabels = self.Settings.Labels.replace(',', ' ').replace('[', ' ').replace(']', ' ')
			userLabels = userLabels.split()
		else:
			userLabels = []
		lenUserLabels = len(userLabels)
		indexLabels = [str(i) for i in range (lenUserLabels,
												lenUserLabels + numCells)]
		cell = row * self.Settings.cols + col
		source = userLabels + indexLabels
		if cell < len(source):
			cellContent = source[cell]
			attribs.text = cellContent
			attribs.textColor = self.Settings.Textcolor
			attribs.textJustify = getattr(JustifyType, 
											self.Settings.Textjustify)
			attribs.textOffsetX = self.Settings.Textoffset[0]
			attribs.textOffsetY = self.Settings.Textoffset[1]
			attribs.fontSizeX = self.par.Fontsize
			attribs.fontFace = 'Verdana'
			# attribs.fontFace = "../vlib/widgets/fonts/Inter-3.13/"\
			# 					"Inter Desktop/Inter-Regular.otf"

			if self.Settings.Type != 'toggledown':
				isSelected = int(self.CurItem[2] == cell)
				attribs.bgColor = [self.Settings.Cellcolor, 
					self.Settings.Cellselectcolor][isSelected]	
			else:
				if col < len(self.Toggles):
					if row < len(self.Toggles[col]):
						toggle = int(self.Toggles[col][row])
					else:
						toggle = 0
				else:
					toggle = 0

				attribs.bgColor = [
					self.Settings.Cellcolor, 
					self.Settings.Cellselectcolor
				][toggle]	

	def OnInitRow(self, row, attribs):
		attribs.rowHeight = self.ownerComp.par.Rowheight
		if row != 0:
			attribs.topBorderOutColor = self.ownerComp.Settings.Bordercolor

	def OnInitCol(self, col, attribs):
		attribs.colWidth = self.ownerComp.par.Colwidth
		if col != 0:
			attribs.leftBorderOutColor = self.ownerComp.Settings.Bordercolor		
 
	def OnSelect(self, startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end):
		# print('start', self.panel.mselect.val, startrow, endrow, start, end)			
		lselect = self.panel.lselect.val
		if self.panel.lselect.val:
			if start:
				self.lselect = True
			self.OnLSelect(startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end)
		elif self.panel.rselect.val:
			if start:
				self.rselect = True
			self.OnRSelect(startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end)	
		elif self.panel.mselect.val:
			if start:
				self.mselect = True	
			self.OnMSelect(startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end)	

		if end:
			if self.lselect:
				self.OnLSelect(startrow, startcol, startcoords, 
						endrow, endcol, endcoords, start, end)
				self.lselect = False
			elif self.rselect:
				self.OnRSelect(startrow, startcol, startcoords, 
						endrow, endcol, endcoords, start, end)	
				self.rselect = False
			elif self.mselect:		
				self.OnMSelect(startrow, startcol, startcoords, 
						endrow, endcol, endcoords, start, end)	
				self.mselect = False

	def OnLSelect(self, startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end):			
		cell = startrow * self.Settings.cols + startcol
		if endrow != None and endcol != None and startrow != -1 and endrow != -1:
			endCell = endrow * self.Settings.cols + endcol
			
			lselect = self.panel.lselect.val
			if start and lselect:
				self.lselect = True
				
			if self.Settings.Type == 'radio':
				if start and self.lselect:
					self.prevState = self.curState
					self.UpdateView(cell)
					self.SetValue(cell)
				elif self.CurItem[2] != endCell and self.lselect:
					self.PrevItem[0:4] = self.CurItem
					prevItemAttribs = self.cellAttribs[self.PrevItem[0], 
						self.PrevItem[1]]
					cellAttribs = self.cellAttribs[endrow, endcol]
					cellAttribs.bgColor = self.Settings.Cellselectcolor
					if prevItemAttribs: 
							prevItemAttribs.bgColor = self.Settings.Cellcolor
					self.CurItem[0:4] = [endrow, endcol, endCell]	
					self.SetValue(endCell)
					self.curState = endCell

			elif self.Settings.Type == 'exclusive':
				if start and self.lselect:
					self.prevState = self.curState
					if cell == self.CurItem[2]:
						cell = -1 	
					self.UpdateView(cell)
					self.SetValue(cell)
				elif self.CurItem[2] != endCell and self.lselect:
					if not end:
						self.PrevItem[0:4] = self.CurItem
						prevItemAttribs = self.cellAttribs[self.PrevItem[0], 
							self.PrevItem[1]]
						cellAttribs = self.cellAttribs[endrow, endcol]
						cellAttribs.bgColor = self.Settings.Cellselectcolor
						if prevItemAttribs: 
								prevItemAttribs.bgColor = self.Settings.Cellcolor
						self.CurItem[0:4] = [endrow, endcol, endCell]	
						self.SetValue(endCell)
						self.curState = endCell

			elif self.Settings.Type == 'toggledown':
				if start and self.lselect:
					state = self.Toggles[startcol][startrow]
					self.prevState = [startcol, startrow, state]
					state = not state
					self.Toggles[startcol][startrow] = state		 
					self.UpdateView(cell)
					value = [startcol, startrow, state]
					self.SetValue(value)
					self.curState = value
					if self.doUndo:
						ui.undo.startBlock(self.undoBlockName)
						ui.undo.addCallback(self.undo, 
												[self.prevState, self.curState])
						ui.undo.endBlock()
				
				elif self.CurItem[2] != endCell and self.lselect:
					self.PrevItem[0:4] = self.CurItem
					state = self.Toggles[endcol][endrow]
					self.prevState = [endcol, endrow, state]
					state = not state
					self.Toggles[endcol][endrow] = state
					self.UpdateView(endCell)
					value = [endcol, endrow, state]
					self.SetValue(value)
					self.curState = value
					self.CurItem[0:4] = [endcol, endrow, endCell]	
					if self.doUndo:
						ui.undo.startBlock(self.undoBlockName)
						ui.undo.addCallback(self.undo, 
												[self.prevState, self.curState])
						ui.undo.endBlock()
				
			else:
				if start and self.lselect:
					self.prevState = self.curState
					self.UpdateView(cell)
					self.SetValue([cell, True])
					self.momentaryCell = cell
				elif self.CurItem[2] != endCell and self.lselect:
					self.PrevItem[0:4] = self.CurItem
					prevItemAttribs = self.cellAttribs[self.PrevItem[0], 
						self.PrevItem[1]]
					cellAttribs = self.cellAttribs[endrow, endcol]
					cellAttribs.bgColor = self.Settings.Cellselectcolor
					if prevItemAttribs: 
							prevItemAttribs.bgColor = self.Settings.Cellcolor
					self.CurItem[0:4] = [endrow, endcol, endCell]
					self.momentaryCell = endCell	
					self.SetValue([self.momentaryCell, True])
					if self.Settings.Type == 'momentary':
						self.SetValue([self.PrevItem[2], False])
				elif end and self.lselect:
					cell = -1 	
					self.UpdateView(cell)
					if self.Settings.Type == 'momentary':
						self.SetValue([self.momentaryCell, False])

			if self.doUndo and end and self.lselect and self.Settings.Type \
								not in ['pulse', 'momentary', 'toggledown']:
				ui.undo.startBlock(self.undoBlockName)
				ui.undo.addCallback(self.undo, [self.prevState, self.curState])
				ui.undo.endBlock()
				self.lselect = False
		
		elif end and self.Settings.Type in ['pulse', 'momentary']:
			cell = -1 	
			self.UpdateView(cell)
			if self.Settings.Type == 'momentary':
				self.SetValue([self.momentaryCell, False])		

		return

	def OnRSelect(self, startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end):	
		if hasattr(self.ownerComp.parent(), 'OnRSelectOffToOn') and start:
			self.ownerComp.parent().OnRSelectOffToOn(
				startrow, startcol, startcoords, 
				endrow, endcol, endcoords, start, end)
		elif hasattr(self.ownerComp.parent(), 'OnRSelectOnToOff') and end:
			self.ownerComp.parent().OnRSelectOnToOff(
				startrow, startcol, startcoords, 
				endrow, endcol, endcoords, start, end)				

	def OnMSelect(self, startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end):	
		if hasattr(self.ownerComp.parent(), 'OnMSelectOffToOn') and start:
			self.ownerComp.parent().OnMSelectOffToOn(
				startrow, startcol, startcoords, 
				endrow, endcol, endcoords, start, end)
		elif hasattr(self.ownerComp.parent(), 'OnMSelectOnToOff') and end:
			self.ownerComp.parent().OnMSelectOnToOff(
				startrow, startcol, startcoords, 
				endrow, endcol, endcoords, start, end)
		if start:
			self.prevrow = None
			self.prevcol = None
		self.row = endrow
		self.col = endcol

		if self.prevrow != None and self.prevcol != None:
			prevCell = self.prevrow * self.Settings.cols + self.prevcol
		else:
			prevCell = None
		if self.row != None and self.col != None:
			cell = self.row * self.Settings.cols + self.col
		else:
			cell = None

		if self.row != self.prevrow or self.col != self.prevcol:
			if cell != None and cell >= 0:
				if self.Settings.Type != 'toggledown':
					state = int(cell == self.CurItem[2])
				else:
					state = int(self.Toggles[self.row][self.col])
				if 	self.cellAttribs[self.row, self.col]: 
					cellAttribs = self.cellAttribs[self.row, self.col]
					cellAttribs.bgColor = [self.Settings.Cellrollcolor, 
						self.Settings.Cellrollselectcolor][state]

			if prevCell != None and prevCell >= 0:
				if self.Settings.Type != 'toggledown':
					state = int(prevCell == self.CurItem[2])
				else:
					state = int(self.Toggles[self.prevrow][self.prevcol])		
				if self.cellAttribs[self.prevrow, self.prevcol]: 
					cellAttribs = self.cellAttribs[self.prevrow, self.prevcol]
					cellAttribs.bgColor = [self.Settings.Cellcolor, 
						self.Settings.Cellselectcolor][state]
		self.prevrow = self.row
		self.prevcol = self.col

	def OnRollover(self, row, col, coords, prevrow, prevcol, prevcoords):
		# print(row, col, coords, prevrow, prevcol, prevcoords)
		if prevrow != None and prevcol != None:
			prevCell = prevrow * self.Settings.cols + prevcol
		else:
			prevCell = None
		if row != None and col != None:
			cell = row * self.Settings.cols + col
		else:
			cell = None

		if row != prevrow or col != prevcol:
			if cell != None and cell >= 0:
				if self.Settings.Type != 'toggledown':
					state = int(cell == self.CurItem[2])
				else:
					state = int(self.Toggles[col][row])
				if 	self.cellAttribs[row, col]: 
					cellAttribs = self.cellAttribs[row, col]
					cellAttribs.bgColor = [self.Settings.Cellrollcolor, 
						self.Settings.Cellrollselectcolor][state]

			if prevCell != None and prevCell >= 0 and len(self.Toggles) > 0:
				if self.Settings.Type != 'toggledown':
					state = int(prevCell == self.CurItem[2])
				else:
					state = int(self.Toggles[prevcol][prevrow])		
				if self.cellAttribs[prevcol, prevrow]: 
					cellAttribs = self.cellAttribs[prevrow, prevcol]
					cellAttribs.bgColor = [self.Settings.Cellcolor, 
						self.Settings.Cellselectcolor][state]	

	def StartEditCell(self, row, col):
		self.ownerComp.setKeyboardFocus(row, col)

	def OnEditCell(self, row, col, value):
		if hasattr(self.ownerComp.parent(), 'OnEditCell'):
			self.ownerComp.parent().OnEditCell(row, col, value)

	def UpdateView(self, value):
		self.curState = value
		if self.Settings.Type != 'toggledown':
			self.PrevItem[0:4] = self.CurItem
			if self.PrevItem[0] != None and self.PrevItem[1] != None:
				prevItemAttribs = self.ownerComp.cellAttribs[self.PrevItem[0], 
															self.PrevItem[1]]
				if prevItemAttribs:
					prevItemAttribs.bgColor = self.ownerComp.pars('Cellcolor*')		
		
		numCols = self.ownerComp.par.cols.eval()
		col = value % numCols
		row = int((value - col) / numCols)
		cellAttribs = self.ownerComp.cellAttribs[row, col]
		if cellAttribs:
			if self.Settings.Type != 'toggledown':
				cellAttribs.bgColor = self.ownerComp.pars('Cellselectcolor*')
			else:
				state = self.Toggles[col][row]	
				cellAttribs.bgColor = [self.Settings.Cellcolor, 
									self.Settings.Cellselectcolor][int(state)]
		self.CurItem[0:4] = [row, col, value]

	def SetValue(self, value):
		self.parent.SetValue(self.ownerComp, value)
		pass

class Timecode(Field):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.tc = vsu.Timecode()
		self.undoBlockName = "Timecode Value"
		self.ownerComp.fetch('curState', self.panel.field.val, 
											search=False, storeDefault=True)
		self.ownerComp.fetch('prevState', self.curState, 
											search=False, storeDefault=True)
		self.prevState = self.curState

	def undo(self, isUndo, info):
		if isUndo:
			state = info[0]
		else:
			state = info[1]
		self.setTimecode(state)

	def setTimecode(self, value):
		timecode = self.tc.StringToTimecode(value, self.prevState)
		self.UpdateView(timecode)
		if self.updateElements:
			[element.UpdateView(value) for element in self.updateElements]
		self.parent.SetValue(self.ownerComp, timecode)

	def OnFocusOffToON(self):
		self.prevState = self.curState

	def OnFocusOnToOff(self):
		value = self.panel.field.val
		if self.prevState != value:
			self.setTimecode(value)
			ui.undo.startBlock(self.undoBlockName)
			ui.undo.addCallback(self.undo, [self.prevState, value])
			ui.undo.endBlock()
			
	def UpdateView(self, value):
		self.curState = value	
		self.textPar.text = value

class Operator(Field):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.tc = vsu.Timecode()
		self.undoBlockName = "Operator Value"
		self.ownerComp.fetch('curState', self.panel.field.val, 
											search=False, storeDefault=True)
		self.ownerComp.fetch('prevState', self.curState, 
											search=False, storeDefault=True)
		self.prevState = self.curState
		self.opStyles = {'CHOP': 'isCHOP', 'COMP': 'isCOMP', 'DAT': 'isDAT', 
						'MAT': 'isMAT', 'object': 'isObject', 
						'panel': 'isPanel', 'SOP': 'isSOP', 'TOP': 'isTOP'}
		self.opTypes = [CHOP, COMP, DAT, MAT, SOP, TOP]
		self.subTypes = ['panel', 'object']

	@property
	def Type(self):
		return self.ownerComp.par.Type.eval()

	@property
	def fromOP(self):
		return self.ownerComp.par.Pathrelativeto.eval()

	def undo(self, isUndo, info):
		if isUndo:
			state = info[0]
		else:
			state = info[1]
		if isinstance(state, OP):
			self.setOP(state.path)

	def OnDrop(self, args):
		style = args[5]
		if style in self.opStyles.keys():
			path = f"{args[6]}/{args[0]}"
			self.setOP(path)

	def setOP(self, path):
		if op(path) != None:
			_op = op(path)
		elif self.fromOP != None:
			if self.fromOP.op(path) != None:
				_op = self.fromOP.op(path)
			else:
				_op = None
		else:
			_op = None

		if _op:
			setValue = False
			_type = self.Type
			if _type == 'OP':
				setValue = True
			else:
				setValue = getattr(_op, self.opStyles[_type])
			if setValue:
				viewPath = _op.path
				if self.fromOP:
					viewPath = _op.path.replace(f"{self.fromOP.path}/", '')	
				self.UpdateView(viewPath, checkPath=False)
				self.parent.SetValue(self.ownerComp, _op)
				self.curState = _op
				ui.undo.startBlock(self.undoBlockName)
				ui.undo.addCallback(self.undo, [self.prevState, _op])
				ui.undo.endBlock()
				self.prevState = self.curState
				return True
		else:
			self.UpdateView('')
			self.parent.SetValue(self.ownerComp, None)
		return False

	def OnFocusOffToON(self):
		pass

	def OnFocusOnToOff(self):
		self.setOP(self.panel.field.val)
	
	def UpdateView(self, value, checkPath=True):
		if checkPath and value != None and value != '':
			if self.fromOP:
				value = value.path.replace(f"{self.fromOP.path}/", '')
		self.curState = value	
		self.textPar.text = value

class ColorSwatch(Element):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.BtnCols = [self.ownerComp.pars('Buttoncolcolor*'),
						self.ownerComp.pars('Buttoncolroll*'),
						self.ownerComp.pars('Buttoncolsel*'),
						self.ownerComp.pars('Buttoncolon*')]
		self.BtnCol = tdu.Dependency(self.BtnCols[0])
		self.swatchColPars = self.ownerComp.pars('Swatchcolor*')

	@property
	def swatchCol(self):
		return [par.eval() for par in self.swatchColPars]
		
	def setColor(self):
		index = min(3, 
			(self.panel.rollover + self.panel.state * 2) + self.panel.lselect)
		self.BtnCol.val = self.BtnCols[index]

	def OnRollOffToOn(self, value):
		self.setColor()

	def OnRollOnToOff(self, value):
		self.setColor()

	def OnLSelect(self, value):
		self.parent.OpenColorPicker(self.swatchCol)
		pass

	# def UpdateView(self, value=None):
	# 	self.setColor()

class ColorSwatches(Element):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.cellAttribs = ownerComp.cellAttribs
		self.CurItem = ownerComp.fetch('CurrentItem', [None, None, None], 
										search=False, storeDefault=True)
		self.PrevItem = ownerComp.fetch('PrevItem', [None, None, None], 
										search=False, storeDefault=True)
		self.parexec = self.ownerComp.op('parexec')
		self.getSettings()
		self.getSwatchesData()
		self.ownerComp.par.reset.pulse()
		self.undoStoreBlockName = "Store Swatch"
		self.ownerComp.fetch('curState', [[0.0, 0.0, 0.0, 1.0], 0, 0], 
											search=False, storeDefault=True)
		self.ownerComp.fetch('prevState', self.curState, 
											search=False, storeDefault=True)
		self.prevState = self.curState
		self.ctrl = False

	def undoStoreSwatch(self, isUndo, info):
		if isUndo:
			state = info[0]
		else:
			state = info[1]
		self.curState = state
		self.Swatches[state[1]][state[2]] = state[0][:5]
		# self.cellAttribs[state[1], state[2]]
		# if self.cellAttribs:
		# 	self.cellAttribs = state[0]
		self.ownerComp.par.reset.pulse()

	def getSwatchesData(self, init=False):
		default = []
		for row in range(self.par.rows.eval()):
			row = []
			for col in range(self.par.cols.eval()):
				row.append([0.0, 0.0, 0.0, 1.0])
			default.append(row)
		if not init:
			self.Swatches = self.ownerComp.fetch('Swatches', default, 
										search=False, storeDefault=True)
		else:
			self.ownerComp.store('Swatches', default)
			self.Swatches = self.ownerComp.fetch('Swatches', search=False)

	def getSettings(self):
		self.Settings = WidgetSettings()
		parNames = self.parexec.par.pars.eval().replace(',', ' ')
		parNames = parNames.split()

		for name in parNames:
			pars = self.ownerComp.pars(name)
			lenPars = len(pars)
			if lenPars > 1:
				value = [par.eval() for par in pars]
				setattr(self.Settings, name.replace('*', ''), value)
			elif lenPars == 1:
				value = pars[0].eval()
				setattr(self.Settings, name, value)

	def UpdateView(self, value):
		self.ownerComp.par.reset.pulse()

	def OnSelect(self, startrow, startcol, startcoords, 
					endrow, endcol, endcoords, start, end):
		if start:
			color = self.Swatches[startrow][startcol][:-1] + [1.0]
			sel = [color[0] + 0.1, color[1] + 0.1, color[2] + 0.1, 1.0]
			if startrow != None and startcol != None:
				cellAttribs = self.cellAttribs[startrow, startcol]
				cellAttribs.bgColor = sel
				if self.panel.lselect and self.panel.ctrl:
					self.ctrl = True
					self.prevState = [self.Swatches[startrow][startcol][:5],
															startrow, startcol]
					self.OnCtrlLSelectSwatch(startrow, startcol)
				elif self.panel.lselect:
					self.parent.SetPrevState()
					self.OnLSelectSwatch(startrow, startcol)
		if end:
			color = self.Swatches[startrow][startcol][:-1] + [1.0]
			if startrow != None and startcol != None:
				cellAttribs = self.cellAttribs[startrow, startcol]
				roll = [color[0] + 0.05, color[1] + 0.05, color[2] + 0.05, 1.0]
				cellAttribs.bgColor = roll
			if self.ctrl:
				self.ctrl = False
				self.curState = [self.Swatches[startrow][startcol][:5], 
															startrow, startcol]
				ui.undo.startBlock(self.undoStoreBlockName)
				ui.undo.addCallback(self.undoStoreSwatch, 
												[self.prevState, self.curState])
				ui.undo.endBlock()					
			else:
				self.parent.AddSelectSwatchCallback()

	def OnLSelectOffToOn(self):
		# if self.panel.ctrl.val:
		# 	self.ctrl = True
		# else:
		# 	self.parent.SetPrevState()
		pass

	def OnLSelectOnToOff(self):
		# if self.ctrl:
		# 	self.ctrl = False

		# else:
		# 	self.parent.AddSelectSwatchCallback()
		pass

	def OnRSelectOffToOn(self):
		pass

	def OnLSelectSwatch(self, row, col):
		value = self.Swatches[row][col]
		self.parent.OnLSelectSwatch(row, col)
		pass

	def OnCtrlLSelectSwatch(self, row, col):
		value = self.Swatches[row][col]
		self.parent.OnCtrlLSelectSwatch(row, col)
		pass

class ColorWheel(Element):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.wheel = ownerComp.op('wheel')
		self.getHS()
		self.getUV(self.h, self.s)
		# self.lSelect = False
		self.undoBlockName = "ColorWheel Values"
		self.ownerComp.fetch('curState', [self.h, self.s], 
											search=False, storeDefault=True)
		self.ownerComp.fetch('prevState', self.curState, 
											search=False, storeDefault=True)
		self.prevState = self.curState

	@property
	def U(self):
		return self.u.val
	@U.setter
	def U(self, value):
		self.u = tdu.Dependency(value)

	@property
	def V(self):
		return self.v.val
	@V.setter
	def V(self, value):
		self.v = tdu.Dependency(value)

	def undo(self, isUndo, info):
		if isUndo:
			state = info[0]
		else:
			state = info[1]
		self.getUV(*state)
		self.parent.OnPick(state)
		self.curState = state

	def pickColor(self):
		self.parent.OnPick(self.getHS())
		self.getUV(self.h, self.s)
		self.curState = [self.h, self.s]

	def getHS(self):
		u = self.panel.u
		v = self.panel.v
		x = 2.0 * u - 1.0
		y = 2.0 * v - 1.0
		self.theta = -math.atan2(-x, y)
		self.r = math.sqrt(math.pow(x, 2.0) + math.pow(y, 2.0))
		self.h = (self.theta + PI) / (PI2)
		self.s = min(1.0, self.r)
		return [self.h, self.s]

	def getUV(self, h, s):
		s = min(1.0, max(0.0, s))
		self.theta = -(h * PI2) - .5 * PI
		self.r = s
		x = self.r * math.cos(self.theta)
		y = self.r * math.sin(self.theta)
		self.U = x * .5 + .5
		self.V = y * .5 + .5

	def OnLSelectOnToOff(self, value):
		# self.lSelect = True
		self.prevState = self.curState
		self.pickColor()
		
	def OnLSelectOffToOn(self, value):
		# self.lSelect = True
		self.pickColor()
		ui.undo.startBlock(self.undoBlockName)
		ui.undo.addCallback(self.undo, [self.prevState, [self.h, self.s]])
		ui.undo.endBlock()

	def OnUV(self, value):
		self.pickColor()
	
	def UpdateView(self, value):
		self.curState = value
		self.getUV(*value)

class ColorPicker(Element):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.wheel = ownerComp.op('wheel')
		self.rgba = ownerComp.op('rgba')
		self.hsv = ownerComp.op('hsv')
		self.value = ownerComp.op('value')
		self.hex = ownerComp.op('hex')
		self.swatch = ownerComp.op('swatch')
		self.swatchColPars = self.swatch.pars('Swatchcolor*')
		self.swatches = ownerComp.op('swatches')
		self.swatchesColors = self.swatches.fetch('Swatches')
		self.ColorWidget = None
		self.color = self.swatchCol
		self.hsva = [0.0, 0.0, 0.0, 1.0] 
		self.window = ownerComp.op('window')
		self.mode = 'RGBA'
		self.disableAlpha = ownerComp.op('disableAlpha')
		self._rgbaMode = tdu.Dependency(ownerComp.op('rgbaMode/Button').panel.state.val)

		self.undoSwatchesSelectBlockName = "Select Swatch"
		self.ownerComp.fetch('prevState', self.hsva[:5], 
											search=False, storeDefault=True)
		self.prevState = self.hsva[:5]

	@property
	def swatchCol(self):
		return [par.eval() for par in self.swatchColPars]

	@property
	def IsOpen(self):
		return self.window.isOpen
	def OpenColorPicker(self):
		pass

	@property
	def _rgba(self):
		return list(colorsys.hsv_to_rgb(*self.hsva[:-1])) + self.hsva[3:4]

	@property
	def RgbaMode(self):
		return self._rgbaMode.val
	
	@RgbaMode.setter
	def RgbaMode(self, value):
		self._rgbaMode.val = value
		self.UpdateViews()

	def undoSelectSwatch(self, isUndo, info):
		if isUndo:
			state = info[0]
		else:
			state = info[1]
		self.hsva = state
		self.UpdateViews()

	def SetPrevState(self):
		self.prevState = self.hsva[:5]
	
	def AddSelectSwatchCallback(self):
		ui.undo.startBlock(self.undoSwatchesSelectBlockName)
		ui.undo.addCallback(self.undoSelectSwatch, 
											[self.prevState, self.hsva[:5]])
		ui.undo.endBlock()		

	def setMode(self):
		tags = self.ColorWidget.tags
		if 'RGBA' in tags:
			self.mode = 'RGBA'
			self.disableAlpha.par.display = False
		else:
			self.mode = 'RGB'
			self.disableAlpha.par.display = True

	def setHsva(self, rgba):
		self.hsva = (list(colorsys.rgb_to_hsv(*rgba[:-1])) + rgba[3:4])

	def undoLinkColorPicker(self, isUndo, info):
		if isUndo:
			state = info[0]
		else:
			state = info[1]
		if state[0] != None:
			self.linkColorPicker(state[0], state[1])

	def linkColorPicker(self, colorWidget, color):
		prevCol = self._rgba if self.mode == 'RGBA' else self._rgba[:-1]
		self.prevColorWidgetInfo = [self.ColorWidget, prevCol]
		self.ColorWidget = colorWidget
		self.setMode()
		if self.mode == 'RGBA':
			rgba = color
		else:
			rgba = color + [1.0]
		self.setHsva(rgba)
		self.UpdateViews(fromView=self.ColorWidget)

	def Open(self, colorWidget, color):
		self.linkColorPicker(colorWidget, color)
		info = [self.prevColorWidgetInfo, [colorWidget, color]]
		ui.undo.startBlock('_HISTORY_HIDE_ Link Color Picker')
		ui.undo.addCallback(self.undoLinkColorPicker, info)
		ui.undo.endBlock()
		self.window.par.winopen.pulse()

	def UpdateColor(self, cp, value, fromView=None):
		rgba = self._rgba
		rgba['rgba'.index(cp)] = value
		self.setHsva(rgba)
		self.UpdateViews(fromView)
	
	def OnValue(self, value):
		self.hsva[2] = value
		self.UpdateViews(self.value)
	
	def OnHex(self, value):
		rgba = self.hexToRgba(value)
		self.setHsva(rgba)
		self.UpdateViews(self.hex)
		# print(value)
	
	def OnHsv(self, cp, value):
		if cp == 'h':
			value /= 360.0
		self.hsva['hsv'.index(cp)] = value
		self.UpdateViews(self.hsv)

	def OnRgba(self, cp, value):
		if self.RgbaMode:
			value = value / 255.0
		rgba = self._rgba
		rgba['rgba'.index(cp)] = value
		self.setHsva(rgba)
		self.UpdateViews(self.rgba)

	def OnPick(self, value):
		self.hsva[0:-2] = value
		self.UpdateViews(self.wheel)
	
	def OnLSelectSwatch(self, row, col):
		rgba = self.swatchesColors[row][col]
		self.setHsva(rgba)
		self.UpdateViews()

	def OnCtrlLSelectSwatch(self, row, col):
		self.swatchesColors[row][col] = self._rgba

	def UpdateViews(self, fromView=None):
		rgba = self._rgba
		for i,cp in enumerate(rgba):
			self.swatchColPars[i].val = cp
		if fromView != self.ColorWidget:
			if self.ColorWidget:
				if self.mode == 'RGBA':
					color = rgba
				else:
					color = rgba[:-1]
				self.setValue(color)
		if fromView != self.rgba:
			_rgba = list(rgba)
			if self.RgbaMode:
				_rgba[0] = int(rgba[0] * 255.0)
				_rgba[1] = int(rgba[1] * 255.0)
				_rgba[2] = int(rgba[2] * 255.0)
				_rgba[3] = int(rgba[3] * 255.0)
			self.rgba.UpdateView(None, _rgba)
		if fromView != self.hsv:
			hsv = list(self.hsva[:-1])
			hsv[0] *= 360
			self.hsv.UpdateView(None, hsv)
		if fromView != self.wheel:
			self.wheel.UpdateView(self.hsva[:-2])
		if fromView != self.value:
			self.value.UpdateView(self.hsva[2])
		if fromView != self.hex:
			self.hex.UpdateView(self.rgbToHex(rgba[:-1]))
		pass

	def setValue(self, color):
		for i,col in enumerate(color):
			VSN.SetVarAttr(self.ColorWidget.ext.WidgetRGBAExt.plugin, 
							self.ColorWidget.ext.WidgetRGBAExt.var.name,
							'rgba'[i], col)			

	def rgbToHex(self, rgb):
		hexR = "%0.2X" % int(rgb[0] * 255)
		hexG = "%0.2X" % int(rgb[1] * 255)
		hexB = "%0.2X" % int(rgb[2] * 255)
		hexStr = hexR + hexG + hexB
		# _hex& 0xFFFFFF
		return hexStr

	def hexToRgba(self, _hex):
		hexColors = [_hex[i:i+2] for i in range(0, len(_hex), 2)]
		rgba = [0.0, 0.0, 0.0] + self.hsva[3:]
		rgba[0] = float.fromhex(hexColors[0]) / 255.0
		rgba[1] = float.fromhex(hexColors[1]) / 255.0
		rgba[2] = float.fromhex(hexColors[2]) / 255.0
		return rgba

class ContextMenu(Element):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.view = ownerComp.op('view')
		self.window = ownerComp.op('window')
		self.list = ownerComp.op('list')
		self.absMouse = ownerComp.par.Absolutemousechop.eval()
		self.menuItems = []
		self.menuLabels = []
		self._CopiedValue = []
		self.obj = None
		self.args = None
		pass

	# TODO put this on Widgets or Vision?	
	@property
	def CopiedValue(self):
		return self._CopiedValue
	@CopiedValue.setter
	def CopiedValue(self, value):
		self._CopiedValue = value

	def OnLSelectOnToOff(self):
		itemIndex = int(self.list.panel.celloverid)
		if itemIndex != -1:
			self.DroplistWidget.OnSelectItem(itemIndex)
			# crashing TD bug... 
			# self.window.par.winclose.pulse()
			run("args[0].pulse()", self.window.par.winclose, delayFrames=3)

	def OpenMenu(self, obj, menuItems, *args):
		self.obj = obj
		self.args = args
		self.menuItems = menuItems
		self.menuLabels = [item['label'] for item in menuItems]
		
		self.list.Settings.Labels = self.menuLabels
		self.list.par.rows = len(self.menuLabels)
		self.list.par.reset.pulse()
		self.view.setFocus()
		self.window.par.winopen.pulse()

	def SetValue(self, element, value):
		itemIndex = value[0]
		self.menuItems[itemIndex]['func'](*self.args)

# TODO add undo block
class Dial(Element):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.over = ownerComp.op('over1')
		self.bgCols = self.GetColors('Dialcolbg', 'Dialcolroll')
		self.knobSwitch = ownerComp.op('switch')
		self.detailLevel = WIDGETS.fetch('detailLevel', 
			{'fine': 1.0, 'init': 1.0, 'prev': 1.0}, 
			storeDefault=True, search=False,)

		self.clampAngleLow = -50
		self.clampAngleHigh = 230

	def getDetailValue(self, value):
		return (self.detailLevel['prev'] 
				+ (value - self.detailLevel['init']) 
				* self.detailLevel['fine'])

	def OnLSelectOffToOn(self):
		self.detailLevel['init'] = self.getAngle()
		fine = 1.0	
		if self.panel.alt.val and self.panel.ctrl.val:
			fine = .001
		elif self.panel.alt.val:
			fine = .01
		elif self.panel.ctrl.val:
			fine = .1
		self.detailLevel['fine'] = fine
		self.par.mouserel = True
		self.panelexecDat.par.valuechange = True
		self.knobSwitch.par.index = 1

	def OnLSelectOnToOff(self):
		self.panelexecDat.par.valuechange = False
		self.par.mouserel = False
		value = self.getAngle()	
		value = self.getDetailValue(value)
		self.detailLevel['prev'] = value
		self.detailLevel['fine'] = 1.0
		self.knobSwitch.par.index = 0


	def getAngle(self):
		if self.par.Rotmode == 'RADIAL':
			u = self.panel.trueu.val
			v = self.panel.truev.val
			angle = math.degrees(math.atan2(u,v)) + 100
			angle = min(self.clampAngleHigh, max(self.clampAngleLow, angle))
		elif self.par.Rotmode == 'VERT':
			angle = self.panel.truev.val * 40
		else:
			angle = self.panel.trueu.val * 40
		return angle

	def OnTrueuv(self, value):
		range1 = self.par.Range1.eval()
		range2 = self.par.Range2.eval()
		Type = self.par.Type
		value = self.getAngle()	
		if self.par.Rotmode != 'RADIAL':	
			value = self.getDetailValue(value)
		self.UpdateView(value, rangeValue=False)
		value = self.RangeVal(self.clampAngleLow, self.clampAngleHigh, 
								range1, range2, value, Type)
		if self.par.Clamp:
			value = min(range2, max(range1, value))
		if self.updateElements:
			[element.UpdateView(value) for element in self.updateElements]
		self.parent.SetValue(self.ownerComp, value)

	def UpdateView(self, value, rangeValue=True):	
		if rangeValue:
			range1 = self.par.Range1
			range2 = self.par.Range2
			value = self.RangeVal(range1, range2, self.clampAngleLow,
				self.clampAngleHigh, value, 'Float')
			self.detailLevel['prev'] = value
		
		if self.par.Clamp:
			value = min(self.clampAngleHigh, max(self.clampAngleLow, value))
		self.over.par.self.r = value

# TODO add undo block
class SpinBox(Element):
	def __init__(self, ownerComp, updateElements=None):
		super().__init__(ownerComp, updateElements)
		self.spinSwitch = ownerComp.op('switch')
		self.multOffset = ownerComp.op('multOffset')
		self.bgCols = self.GetColors('Slidercolbg', 'Slidercolroll')
		self.knobCols = self.GetColors('Knobcolbg', 'Knobcolsel')
		self.detailLevel = ownerComp.fetch('detailLevel', 
			{'fine': 1.0, 'init': 1.0, 'prev': 1.0}, 
			storeDefault=True, search=False,)
		self.prevValue = self.panel.truev.val

	def getDetailValue(self, value):
		return (self.detailLevel['prev'] 
				+ (value - self.detailLevel['init']) 
				* self.detailLevel['fine'])

	def OnLSelectOffToOn(self):
		fine = 1.0	
		self.par.mouserel = True
		self.detailLevel['init'] = self.panel.truev.val * self.par.Relposscale
		if self.panel.alt.val and self.panel.ctrl.val:
			self.par.mouserel = True
			fine = .001
		elif self.panel.alt.val:
			self.par.mouserel = True
			fine = .01
		elif self.panel.ctrl.val:
			self.par.mouserel = True
			fine = .1
		self.detailLevel['fine'] = fine
		self.spinSwitch.par.index = 1

	def OnLSelectOnToOff(self):
		self.par.mouserel = False
		value = self.panel.truev.val * self.par.Relposscale		
		value = self.getDetailValue(value)	
		if self.par.Clamp:
			value = min(1, max(0, value))
		self.detailLevel['prev'] = value
		self.detailLevel['fine'] = 1.0
		self.spinSwitch.par.index = 0

	def OnTruev(self, value):
		range1 = self.par.Range1.eval()
		range2 = self.par.Range2.eval()
		Type = self.par.Type
		value *= self.par.Relposscale		
		value = self.getDetailValue(value)
		if self.par.Clamp:
			value = min(1, max(0, value))
		self.UpdateView(value, rangeValue=False)
		value = self.ExpandVal(range1, range2, value, Type)
		if self.updateElements:
			[element.UpdateView(value) for element in self.updateElements]
		
		if value != self.prevValue:
			self.spinSwitch.par.index = int(value > self.prevValue) + 1
		self.parent.SetValue(self.ownerComp, value)
		self.prevValue = value

	def UpdateView(self, value, rangeValue=True):
		if not rangeValue:
			self.multOffset.par.ty = value
		else:
			range1 = self.par.Range1
			range2 = self.par.Range2
			value = self.ownerComp.NormalizeVal(range1, range2, value)
			self.detailLevel['prev'] = value

def SetValue(widget, value):
	# placeholder function so widget inside of Widgets function have 
	# a function to call when testing them
	# print(widget, value)
	pass
