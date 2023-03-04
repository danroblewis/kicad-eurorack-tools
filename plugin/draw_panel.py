import pcbnew

def nnline(a, b, stroke=0.5):
	box = pcbnew.PCB_SHAPE()
	box.SetLayer(pcbnew.Edge_Cuts)
	box.SetShape(pcbnew.S_SEGMENT)
	box.SetStart(pcbnew.VECTOR2I(int(a[0]*pcbnew.schIUScale.mmToIU(100)),int(a[1]*pcbnew.schIUScale.mmToIU(100))))
	box.SetEnd(pcbnew.VECTOR2I(int(b[0]*pcbnew.schIUScale.mmToIU(100)),int(b[1]*pcbnew.schIUScale.mmToIU(100))))
	box.SetWidth(int(stroke*pcbnew.schIUScale.mmToIU(100)))
	pcbnew.GetBoard().Add(box)


def nnrect(pos, dims, stroke=0.5):
	box = pcbnew.PCB_SHAPE()
	box.SetLayer(pcbnew.Edge_Cuts)
	box.SetShape(pcbnew.S_RECT)
	box.SetStart(pcbnew.VECTOR2I(int(pos[0]*pcbnew.schIUScale.mmToIU(100)), int(pos[1]*pcbnew.schIUScale.mmToIU(100))))
	box.SetEnd(pcbnew.VECTOR2I(int((pos[0]+dims[0])*pcbnew.schIUScale.mmToIU(100)), int((pos[1]+dims[1])*pcbnew.schIUScale.mmToIU(100))))
	box.SetWidth(int(stroke*pcbnew.schIUScale.mmToIU(100)))
	pcbnew.GetBoard().Add(box)



def nnzone(pos, dims, layername):
	board = pcbnew.GetBoard()
	nets = board.GetNetsByName()
	gnd_net = nets.find("GND").value()[1]  # this is a NETINFO_ITEM

	layertable = {}
	for i in range(pcbnew.PCB_LAYER_ID_COUNT):
	    layertable[board.GetLayerName(i)] = i  # this is an integer

	newarea = board.AddArea(
		None, 
		gnd_net.GetNetCode(), 
		layertable[layername], 
		pcbnew.VECTOR2I(int(pos[0]*pcbnew.schIUScale.mmToIU(100)),int(pos[1]*pcbnew.schIUScale.mmToIU(100))), 
		pcbnew.ZONE_BORDER_DISPLAY_STYLE_DIAGONAL_EDGE
	)
	newoutline = newarea.Outline()
	# newoutline.Append(int(pos[0]*pcbnew.schIUScale.mmToIU(100)),int(pos[1]*pcbnew.schIUScale.mmToIU(100)))
	newoutline.Append(int((pos[0]+dims[0])*pcbnew.schIUScale.mmToIU(100)),int(pos[1]*pcbnew.schIUScale.mmToIU(100)))
	newoutline.Append(int((pos[0]+dims[0])*pcbnew.schIUScale.mmToIU(100)),int((pos[1]+dims[1])*pcbnew.schIUScale.mmToIU(100)))
	newoutline.Append(int(pos[0]*pcbnew.schIUScale.mmToIU(100)),int((pos[1]+dims[1])*pcbnew.schIUScale.mmToIU(100)))
	newarea.HatchBorder()


def nncircle(pos, diameter, stroke=0.5):
	circle = pcbnew.PCB_SHAPE()
	circle.SetLayer(pcbnew.Edge_Cuts)
	circle.SetShape(pcbnew.S_CIRCLE)
	pts = [
		(pos[0],pos[1]),
		(pos[0],pos[1]+diameter/2.0)
	]

	circle.SetStart(pcbnew.VECTOR2I(int(pts[0][0]*pcbnew.schIUScale.mmToIU(100)), int(pts[0][1]*pcbnew.schIUScale.mmToIU(100))))
	circle.SetEnd(pcbnew.VECTOR2I(int(pts[1][0]*pcbnew.schIUScale.mmToIU(100)), int(pts[1][1]*pcbnew.schIUScale.mmToIU(100))))

	circle.SetWidth(int(stroke*pcbnew.schIUScale.mmToIU(100)))
	pcbnew.GetBoard().Add(circle)


def draw_euro_panel(hp, snaps=True):
	onehp = 5.08

	ax = 20
	ay = 20
	width = hp*onehp
	height = 128.5
	screwsize = 3.2
	betweenscrews = 122.5
	screwtopoffset = 3

	board = pcbnew.GetBoard()

	nnrect((ax, ay), (width, height))
	nnzone((ax, ay), (width, height), 'F.Cu')
	nnzone((ax, ay), (width, height), 'B.Cu')

	# there should be 2 or 4 screw holes. if the module is 2hp, just draw them in the middle
	if hp <= 2:
		nncircle((ax + width/2, ay + screwtopoffset), screwsize)
		nncircle((ax + width/2, ay + screwtopoffset + betweenscrews), screwsize)
	else:
		# the edge of the circle should be 5.08mm from the edge of the board
		# so the center of the circle should be edge + 5.08 + screwsize/2
		space_from_edge = onehp + screwsize/2
		nncircle((ax + space_from_edge, ay + screwtopoffset), screwsize)
		nncircle((ax + width - space_from_edge, ay + screwtopoffset), screwsize)
		nncircle((ax + space_from_edge, ay + screwtopoffset + betweenscrews), screwsize)
		nncircle((ax + width - space_from_edge, ay + screwtopoffset + betweenscrews), screwsize)

	if snaps:
		backplaneheight = 109
		bx = ax
		by = ay + int((height-backplaneheight)/2)

		# space out cut-lines every 1hp
		# that's 2mm connected, 3mm not connected
		# that's 5mm wide each time
		cut_spacing = 5
		for ly in [by, by+backplaneheight]:
			for lx in range(int(ax), int(ax+width-4), 5):
				nnline(
					(1.5+lx, ly),
					(1.5+lx + 3, ly)
				)

	# TODO: widen the mounting holes with arcs+lines so they fit better with any case design.
	# TODO: group all of the objects so people can delete them easier

	pcbnew.Refresh()


# TODO: write a function to create a frontpanel to the right with mounting holes in the appropriate places for the pots, jacks, and leds
def draw_euro_frontpanel(hp):
	board = pcbnew.GetBoard()
	fs = board.GetFootprints()
	pots = [ f for f in fs if 'Potentiometer' in f.GetDescription() ]
	jacks = [ f for f in fs if 'Thonkiconn' in f.GetDescription() ]

	for jack in jacks:
		c = jack.GetCenter()
		x = c[0] / pcbnew.schIUScale.mmToIU(100)
		y = c[1]  / pcbnew.schIUScale.mmToIU(100)
		# TODO: find the rotation of the jack, adjust circle position accordingly
		nncircle((x+0.7,y), 5)

	pcbnew.Refresh()



