import wx
import pcbnew
import math


def scale(d):
    return d/(100000*2)


def draw_rect(dc, x, y, w, h, angle):
    pts = [
        (-w/2, -h/2),
        (w/2, -h/2),
        (w/2, h/2),
        (-w/2, h/2),
        (-w/2, -h/2),
    ]
    npts = []
    for dx, dy in pts:
        npts.append((
            scale(x + dx * math.cos(angle) - dy*math.sin(angle)),
            scale(y + dy * math.cos(angle) + dx*math.sin(angle)),
        ))
    dc.DrawPolygon(npts)


def draw_poly(dc, x, y, pts, angle):
    npts = []
    for dx, dy in pts:
        npts.append((
            scale(x + dx * math.cos(angle) - dy*math.sin(angle)),
            scale(y + dy * math.cos(angle) + dx*math.sin(angle)),
        ))
    dc.DrawPolygon(npts)


class Pad:
    def __init__(self, part, pad):
        dx = pad.GetCenter().x - part.x
        dy = pad.GetCenter().y - part.y
        # self.x = part.x + dx * math.cos(part.angle) - dy * math.sin(part.angle)
        # self.y = part.y + dy * math.cos(part.angle) + dx * math.sin(part.angle)
        self.x = pad.GetCenter().x
        self.y = pad.GetCenter().y
        self.width = pad.GetBoundingBox().GetWidth()
        self.height = pad.GetBoundingBox().GetHeight()
        self.angle = part.angle
        self.netname = pad.GetNetname()
        self.name = pad.GetName()
        self.part = part
        # if part.name == 'J1':
        #     print(self.name, '\t', self.x, '\t', self.y)


    def draw(self, dc):
        pts = [
            (-self.width/2, -self.height/2),
            ( self.width/2, -self.height/2),
            ( self.width/2,  self.height/2),
            (-self.width/2,  self.height/2),
            (-self.width/2, -self.height/2),
        ]
        draw_poly(dc, self.x, self.y, pts, self.angle)


class Part:
    def __init__(self, footprint):
        self._angle = math.radians(footprint.GetOrientationDegrees())
        self.name = footprint.GetReference()
        self.x = footprint.GetCenter().x
        self.y = footprint.GetCenter().y
        self._angle = math.radians(footprint.GetOrientationDegrees())
        self.angle = 0
        self.width = footprint.GetCourtyard(0).Outline(0).GetCachedBBox().GetWidth()
        self.height = footprint.GetCourtyard(0).Outline(0).GetCachedBBox().GetHeight()
        # self.width = footprint.GetBoundingBox().GetWidth()
        # self.height = footprint.GetBoundingBox().GetHeight()
        self.footprint = footprint

        if self.name == 'J1':
            print()
            print(self.name, '\t', self.x, '\t', self.y, '\t', self.width, '\t', self.height)

        self.pads = [ Pad(self, p) for p in list(footprint.Pads()) ]


    def draw(self, dc):
        pts = [
            (-self.width/2, -self.height/2),
            ( self.width/2, -self.height/2),
            ( self.width/2,  self.height/2),
            (-self.width/2,  self.height/2),
            (-self.width/2, -self.height/2),
        ]
        draw_poly(dc, self.x, self.y, pts, self.angle)
        for pad in self.pads:
            pad.draw(dc)


class AutoplacerUWindow(wx.Dialog):
    def __init__(self, *args, **kw):
        super(AutoplacerUWindow, self).__init__(*args, style=wx.RESIZE_BORDER|wx.CAPTION|wx.CLOSE_BOX, **kw)

        self.exclude_types = [ 'U', 'J', 'Q', 'S' ]
        self.SetSize(wx.Size(800, 1200))
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.Bind(wx.EVT_CLOSE, self.quit_dialog)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase)
        self.Center()
        self.Show(True)
        self.Bind(wx.EVT_LEFT_DOWN, self.onleftclick)
        self.Bind(wx.EVT_RIGHT_DOWN, self.onrightclick)
        self.SetDoubleBuffered(True)

        self.timer = wx.Timer(self)
        self.timer.Start(50) #Generate a timer event every second
        self.timeToLive = 100
        self.Bind(wx.EVT_TIMER, self.timer_handle, self.timer)

        self.load()


    def load(self):
        board = pcbnew.GetBoard()

        self.parts = [ Part(f) for f in pcbnew.GetBoard().GetFootprints() ]

        nets = {}
        for part in self.parts:
            if 'IDC' in part.footprint.GetDescription():
                continue
            for pad in part.pads:
                # if pad.netname in [ 'GND', '+5V', '-12V', '+12V' ]:
                #     continue
                if pad.netname not in nets:
                    nets[pad.netname] = []
                nets[pad.netname].append(pad)
        self.nets = nets
        self.resolve_placements()


    def resolve_placements(self):
        ics = [ p for p in self.parts if p.name[0] == 'U' ]
        pads = []
        for ic in ics:
            for pad in ic.pads:
                pads.append(pad)

        exclude_nets = [ 'GND', '+12V', '-12V', '+5V' ]
        movables = []
        for p in self.parts:
            print(p.name[0])
            if p.name[0] not in self.exclude_types:
                movables.append(p)

        for part in movables:
            if part.x < 90000000:
                continue
            print(part.x)
            # find a pad that is connected to an IC
            connected_pad = None
            for pad in part.pads:
                if pad.netname in exclude_nets:
                    continue
                netpads = self.nets[pad.netname]
                for npad in netpads:
                    if npad.part.name[0] == 'U':
                        connected_pad = npad
            if connected_pad == None:
                continue
            
            # get orientation of pad
            conn_orient = 'vert'
            if connected_pad.width > connected_pad.height:
                conn_orient = 'horiz'

            dir_y = 0
            dir_x = 0
            if conn_orient == 'vert':
                dir_y = 1 if connected_pad.y > connected_pad.part.y else -1
            else:
                dir_x = 1 if connected_pad.x > connected_pad.part.x else -1
            part.x = connected_pad.x + dir_x*pad.part.width
            part.y = connected_pad.y + dir_y*pad.part.height

            pad_orient = 'vert'
            if pad.part.width > pad.part.height:
                pad_orient = 'horiz'

            # print(part.name, '\t', pad.name, '\t', connected_pad.part.name, '\t', connected_pad.name, '\t', pad.netname, '\t', pad.width, '\t', pad.height, '\t', pad_orient, '\t', conn_orient, '\t', dir_x, '\t', dir_y)

            if pad_orient != conn_orient:
                # rotate 90deg
                # print('rotating')
                # print(pad.part.angle)
                pad.part.angle += math.radians(90)
                # print(pad.part.angle)

        self.update_board()
        # get pins for all ICs
        # get nets for those pins
        # get parts connected to those nets
        # choose the first IC from the list of ICs connected to the net
        # get the x,y position and bounding box of the IC pin
        # set the orietation of the part to be the same orientation as the IC pin, with the pin of the part facing the pin of the IC
        # set the x,y position of the part to be aligned with the pin, 3mm away from the pin


    def onleftclick(self, event=None):
        self.on_paint()


    def update_board(self):
        # print("updating")
        for part in self.parts:
            if part.name[0] in self.exclude_types:
                continue
            # if 'IDC' in part.footprint.GetDescription():
            #    print(part.name, '\t', part.x, '\t', part.y, '\t', math.degrees(part.angle))
            x = part.x
            y = part.y
            # move back a bit if its a thonk
            # if "Thonk" in part.footprint.GetDescription(): # and 'JOUT1' in part.footprint.GetReference():
            #     dy = -60
            #     dx = 3
            #     a = -part.body.angle - part._angle
            #     x = x + dx * math.cos(a) - dy * math.sin(a)
            #     y = y + dy * math.cos(a) + dx * math.sin(a)

            try:
                part.footprint.SetPosition(pcbnew.VECTOR2I(int(x),int(y)))
                # print('orienting part', part.name, math.degrees(part.angle) % 360)

                part.footprint.SetOrientationDegrees(math.degrees(part.angle) % 360)
            except Exception as e:
                print(e)
                pass
        pcbnew.Refresh()


    def onrightclick(self, event=None):
        print('right')
        # write states to board
        self.update_board()


    def timer_handle(self, event=None):
        # self.update_board()
        # self.Refresh()
        pass


    def on_paint(self, event=None): 
        dc = wx.BufferedPaintDC(self)
        dc.Clear()
        dc.SetPen(wx.Pen(wx.BLACK, 2))

        for p in self.parts:
            p.draw(dc)

        # draw nets
        for netname in self.nets:
            for p1 in self.nets[netname]:
                for p2 in self.nets[netname]:
                    if p1 == p2:
                        continue
                    # draw line between two points
                    dc.SetPen(wx.Pen((50,50,50)))
                    dc.DrawLine(p1.x, p1.y, p2.x, p2.y)


    def on_erase(self, event):
        """ This is intentionally empty to avoid flicker! """
        pass


    def quit_dialog(self, e):
        self.Destroy()
        self.EndModal(0)




        # dc = wx.PaintDC(self) 
        # brush = wx.Brush("white")  
        # dc.SetBackground(brush)  
        # dc.Clear() 

        # # dc.DrawBitmap(wx.Bitmap("python.jpg"),10,10,True) 
        # # color = wx.Colour(255,0,0)
        # # b = wx.Brush(color) 

        # dc.SetBrush(b) 
        # dc.DrawCircle(300,125,50) 
        # dc.SetBrush(wx.Brush(wx.Colour(255,255,255))) 
        # dc.DrawCircle(300,125,30) 

        # pen = wx.Pen(wx.Colour(0,0,255)) 
        # dc.SetPen(pen) 
        # dc.DrawLine(200,50,350,50) 
        # dc.SetBrush(wx.Brush(wx.Colour(0,255,0), wx.CROSS_HATCH)) 

# cd "C:\Program Files\KiCad\7.0\bin\"; .\pcbnew.exe "C:\Users\danie\OneDrive\Documents\Kicad Projects\wis designs\passive mult\passive mult.kicad_pcb"

