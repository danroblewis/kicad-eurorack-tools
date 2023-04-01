import wx
import pcbnew
import math
import pymunk


def scale(d):
    return d/(100000)

def downscale(d):
    return d/2

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
            x + dx * math.cos(angle) - dy*math.sin(angle),
            y + dy * math.cos(angle) + dx*math.sin(angle),
        ))
    dc.DrawPolygon(npts)


def draw_poly(dc, x, y, pts, angle):
    npts = []
    for dx, dy in pts:
        npts.append((
            x + dx * math.cos(angle) - dy*math.sin(angle),
            y + dy * math.cos(angle) + dx*math.sin(angle),
        ))
    dc.DrawPolygon(npts)


class Pad:
    def __init__(self, part, pad):
        dx = scale(pad.GetCenter().x) - part.x
        dy = scale(pad.GetCenter().y) - part.y
        self.x = part.x + dx * math.cos(part.angle) - dy * math.sin(part.angle)
        self.y = part.y + dy * math.cos(part.angle) + dx * math.sin(part.angle)
        self.width = scale(pad.GetBoundingBox().GetWidth())
        self.height = scale(pad.GetBoundingBox().GetHeight())
        self.angle = part.angle
        self.netname = pad.GetNetname()
        self.name = pad.GetName()

        self.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        self.body.position = self.x, self.y
        self.poly = pymunk.Poly.create_box(self.body, (self.width, self.height))
        self.poly.mass = 10
        self.body.poly = self.poly

        self.joints = []
        pj = pymunk.constraints.PivotJoint(part.body, self.body, (dx,dy), (0,0))
        pj.collide_bodies = False
        self.joints.append(pj)
        pj = pymunk.constraints.PivotJoint(part.body, self.body, (dx+10,dy), (10,0))
        pj.collide_bodies = False
        self.joints.append(pj)
        gj = pymunk.constraints.GearJoint(part.body, self.body, 0, 1.0)
        gj.collide_bodies = False
        self.joints.append(gj)


    def draw(self, dc):
        pts = self.poly.get_vertices()
        pts = [ (downscale(x), downscale(y)) for x,y in pts ]
        x,y = self.body.position
        draw_poly(dc, downscale(x), downscale(y), pts, self.body.angle)


class Part:
    def __init__(self, footprint):
        self._angle = math.radians(footprint.GetOrientationDegrees())
        self.name = footprint.GetReference()
        self.x = scale(footprint.GetCenter().x)
        self.y = scale(footprint.GetCenter().y)
        self.angle = math.radians(footprint.GetOrientationDegrees())
        self.width = scale(footprint.GetCourtyard(0).Outline(0).GetCachedBBox().GetWidth())
        self.height = scale(footprint.GetCourtyard(0).Outline(0).GetCachedBBox().GetHeight())
        self.footprint = footprint

        # if 'IDC' in footprint.GetDescription() or 'Thonk' in footprint.GetDescription(): # or footprint.GetReference()[0] == 'U':
        if False:
            self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        else:
            self.body = pymunk.Body()
        self.body.position = self.x, self.y
        self.poly = pymunk.Poly.create_box(self.body, (self.width, self.height))
        self.poly.mass = 10

        self.body.poly = self.poly
        self.pads = [ Pad(self, p) for p in list(footprint.Pads()) ]


    def draw(self, dc):
        pts = self.poly.get_vertices()
        pts = [ (downscale(x), downscale(y)) for x,y in pts ]
        x,y = self.body.position
        draw_poly(dc, downscale(x), downscale(y), pts, self.body.angle)
        for pad in self.pads:
            pad.draw(dc)


class AutoplacerWindow(wx.Dialog):
    def __init__(self, *args, **kw):
        super(AutoplacerWindow, self).__init__(*args, style=wx.RESIZE_BORDER|wx.CAPTION|wx.CLOSE_BOX, **kw)

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

        self.space = pymunk.Space()      # Create a Space which contain the simulation
        self.space.gravity = 0,281       # Set its gravity
        self.space.gravity = 0,0       # Set its gravity

        for part in self.parts:
            self.space.add(part.body, part.poly)
            for pad in part.pads:
                self.space.add(pad.body, pad.poly)
                for joint in pad.joints:
                    self.space.add(joint)

        nets = {}
        for part in self.parts:
            if 'IDC' in part.footprint.GetDescription():
                continue
            for pad in part.pads:
                # if pad.netname in [ 'GND', '+5V', '-12V', '+12V' ]:
                #     continue
                if pad.netname not in nets:
                    nets[pad.netname] = []
                nets[pad.netname].append(pad.body)
        for netname in nets:
            for p1 in nets[netname]:
                for p2 in nets[netname]:
                    if p1 == p2:
                        continue
                    joint = pymunk.constraints.DampedSpring(p1, p2, (0,0), (0,0), 1, 10, 0)
                    self.space.add(joint)
        self.nets = nets

        self.walls = []
        def make_static_box(x, y, w, h):
            b = pymunk.Body(body_type=pymunk.Body.STATIC)
            b.position = x, y
            p = pymunk.Poly(b, [ (0,0), (w,0), (w,h), (0,h), (0,0) ])
            b.poly = p
            self.space.add(b, p)
            self.walls.append((b,p))

        ds = pcbnew.GetBoard().GetDrawings()
        eds = [ d for d in ds if d.GetLayerName() == 'Edge.Cuts' ]
        wallbox = next(d for d in ds if d.GetLayerName() == 'Edge.Cuts' and d.GetShape() == 1).GetBoundingBox()
        

        offset = 5000
        snapoff_size = 120
        l = scale(wallbox.GetLeft())
        r = scale(wallbox.GetRight())
        t = scale(wallbox.GetTop())
        b = scale(wallbox.GetBottom())
        w = scale(wallbox.GetWidth())
        h = scale(wallbox.GetHeight())
        
        self.wallbox = wallbox

        make_static_box( # top left, right
            l-offset, t-offset+snapoff_size,
            w+offset*2, offset
        )
        make_static_box( # top left, down
            l-offset, t-offset,
            offset, h+offset*2
        )
        make_static_box( # bottom left, right
            l-offset, b-snapoff_size,
            w+offset*2, b+offset
        )
        make_static_box( # top right, down
            r, t-offset,
            offset, h+offset*2
        )



    def onleftclick(self, event=None):
        # apply impulse force to all bodies
        impulse_amount = -5000
        for part in self.parts:
            # if 'IDC' in part.footprint.GetDescription() or 'Thonk' in part.footprint.GetDescription(): # or part.footprint.GetReference()[0] == 'U':
            #     continue
            dx = part.body.position.x - event.X
            dy = part.body.position.y - event.Y
            x_amount = impulse_amount * max(1,1/(dx*dx))
            y_amount = impulse_amount * max(1,1/(dy*dx))
            part.body.apply_impulse_at_world_point((x_amount,y_amount), (event.X,event.Y))
        self.on_paint()


    def update_board(self):
        print("updating")
        for part in self.parts:
            x = part.body.position.x
            y = part.body.position.y
            # move back a bit if its a thonk
            if "Thonk" in part.footprint.GetDescription(): # and 'JOUT1' in part.footprint.GetReference():
                dy = -60
                dx = 3
                a = -part.body.angle - part._angle
                x = x + dx * math.cos(a) - dy * math.sin(a)
                y = y + dy * math.cos(a) + dx * math.sin(a)

            x = x * pcbnew.schIUScale.mmToIU(1) * 10
            y = y * pcbnew.schIUScale.mmToIU(1) * 10
            s = 50 * pcbnew.schIUScale.mmToIU(1) * 10
            # if "Thonk" in part.footprint.GetDescription():
            #     print('thonking', s)
            #     x -= s * math.cos(-part.body.angle) - s * math.sin(-part.body.angle)
            #     y -= s * math.cos(-part.body.angle) + s * math.sin(-part.body.angle)
            #     # x -= - s * math.sin(-part.body.angle)
            #     # y -= s * math.sin(-part.body.angle)
            # x += self.wallbox.GetLeft()
            # y += self.wallbox.GetTop()
            y += 1000
            try:
                part.footprint.SetPosition(pcbnew.VECTOR2I(int(x),int(y)))
                part.footprint.SetOrientationDegrees(math.degrees(-part.body.angle + part._angle) % 360)
            except:
                pass
        pcbnew.Refresh()


    def onrightclick(self, event=None):
        print('right')
        # write states to board
        self.update_board()


    def timer_handle(self, event=None):
        for i in range(10):
            self.space.step(0.001)
        self.update_board()
        self.Refresh()


    def on_paint(self, event=None): 
        dc = wx.BufferedPaintDC(self)
        dc.Clear()
        dc.SetPen(wx.Pen(wx.BLACK, 2))

        for p in self.parts:
            p.draw(dc)

        for b, p in self.walls:
            x, y = b.position
            pts = p.get_vertices()
            pts = [ (downscale(x), downscale(y)) for x,y in pts ]
            draw_poly(dc, downscale(x), downscale(y), pts, 0)

        # draw nets
        for netname in self.nets:
            for p1 in self.nets[netname]:
                for p2 in self.nets[netname]:
                    if p1 == p2:
                        continue
                    # draw line between two points
                    dc.SetPen(wx.Pen((50,50,50)))
                    dc.DrawLine(downscale(p1.position.x), downscale(p1.position.y), downscale(p2.position.x), downscale(p2.position.y))


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

