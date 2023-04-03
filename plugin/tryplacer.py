import wx
import pcbnew
import math



def unscale(d):
    return d*pcbnew.schIUScale.mmToIU(1)


class TryPlacer(wx.Dialog):
    """
    Goal: place parts in a reasonable spot on the page
    Assume: the jacks, pots, and chips are spaced out. maybe dont assume that. maybe just move them so they are spaced out.
    Steps:
    1. find all jacks, knobs, transistors, and chips. place them vertically on the work area, orient up, with some spacing between eachother, refresh board
    2. pull new position values for these parts
    3. get list of 'moveable' parts
    4. make empty list of spare_parts
    4. for each moveable part:
        1. for each pad:
            1. if the pad is directly connected to a power pin, ignore it
            2. if the pad is connected to a jack, add it to a list of that jack's pin's parts
            2. if the pad is connected to a jack, add it to a list of that jack's pin's parts
            3. if the pad is connected to a chip, add it to a list of that chip's pin's parts
            4. if the pad is connected to a transistor, add it to a list of that transistor's pin's parts
            5. if none of these have happened, try the next pad
        2. if the part has not been assigned to any pin, add it to spare_parts list
    5. for each jack, knob, transistor, and chip:
        1. for each of their pins
            1. get list of parts connected to it
            2. determine orientation of source pin
            3. make variable curr_width = 0
            4. for each part on the pin:
                1. match part orientation with source pin
                2. determine direction of offset (if the source pin is to the right or left of the source part)
                3. place part width/2+offset in the direction of the offset
                4. increase curr_width to include the part's full width + offset
    """
    def Run(self):
        self.load()

    def load(self):
        self.resolve_placements()


    def resolve_placements(self):
        power_nets = [ '+5V', '+12V', 'GND', '-12V' ]

        footprints = pcbnew.GetBoard().GetFootprints()
        # step 1: place big parts
        big_part_types = [ 'U', 'J', 'Q', 'S' ]
        big_parts = []
        for part in footprints:
            if part.GetReference()[0] in big_part_types:
                big_parts.append(part)
            elif 'AlphaPot' in part.GetValue():
                big_parts.append(part)

        offset = int(unscale(2000))
        xoffset = int(unscale(10000))
        spacer = int(unscale(100))
        big_part_pads = {}
        for part in big_parts:
            part.SetOrientationDegrees(0)
            # posx, posy = part.GetPosition()
            # topy = part.GetBoundingBox().GetTop()
            # dy = posy - topy
            # part.SetPosition(pcbnew.VECTOR2I(xoffset, spacer+offset+dy))
            # offset = part.GetBoundingBox().GetBottom() + spacer
            # pcbnew.Refresh()
            for pad in part.Pads():
                netname = pad.GetNetname()
                if any(pn in netname for pn in power_nets):
                    continue
                if netname not in big_part_pads:
                    big_part_pads[netname] = []
                big_part_pads[netname].append(pad)


        spare_parts = []


        """
        4. for each moveable part:
            1. for each pad:
                1. if the pad is directly connected to a power pin, ignore it
                2. if the pad is connected to a jack, add it to a list of that jack's pin's parts
                2. if the pad is connected to a jack, add it to a list of that jack's pin's parts
                3. if the pad is connected to a chip, add it to a list of that chip's pin's parts
                4. if the pad is connected to a transistor, add it to a list of that transistor's pin's parts
                5. if none of these have happened, try the next pad
            2. if the part has not been assigned to any pin, add it to spare_parts list
        5. for each jack, knob, transistor, and chip:
            1. for each of their pins
                1. get list of parts connected to it
                2. determine orientation of source pin
                3. make variable curr_width = 0
                4. for each part on the pin:
                    1. match part orientation with source pin
                    2. determine direction of offset (if the source pin is to the right or left of the source part)
                    3. place part width/2+offset in the direction of the offset
                    4. increase curr_width to include the part's full width + offset

        """
        movable_part_types = [ 'R', 'C', 'L', 'D' ]
        movable_parts = []
        for f in footprints:
            if f in big_parts:
                continue
            if f.GetReference()[0] in movable_part_types:
                movable_parts.append(f)

        parts_applied = {}
        for part in movable_parts:
            for pad in part.Pads():
                netname = pad.GetNetname()
                if any(pn in netname for pn in power_nets):
                    continue
                
                if netname not in big_part_pads:
                    continue

                bpads = big_part_pads[netname]
                # if connected to a jack, prefer that
                thonks = [ bpad for bpad in bpads if 'Thonk' in bpad.GetParent().GetValue() ]
                pots = [ bpad for bpad in bpads if 'AlphaPot' in bpad.GetParent().GetValue() ]
                chips = [ bpad for bpad in bpads if bpad.GetParent().GetReference()[0] == 'U' ]
                trans = [ bpad for bpad in bpads if bpad.GetParent().GetReference()[0] == 'Q' ]
                if len(thonks) > 0:
                    bpad = thonks[0]
                    print("use thonk for " + part.GetReference())
                elif len(pots) > 0:
                    bpad = pots[0]
                    print("use pot for " + part.GetReference())
                elif len(chips) > 0:
                    bpad = chips[0]
                    print("use chip for " + part.GetReference())
                elif len(trans) > 0:
                    bpad = trans[0]
                    print("use chip for " + part.GetReference())
                else:
                    print("use nothing for " + part.GetReference())
                    continue

                bpart = bpad.GetParent()

                pad_id = f"{bpart.GetReference()}_{bpad.GetName()}"
                if pad_id not in parts_applied:
                    parts_applied[pad_id] = 0
                else:
                    parts_applied[pad_id] += 1

                # get center of big parent parent
                # figure out which direction we're going
                bpartx, bparty = bpart.GetPosition()
                bpadx, bpady = bpad.GetPosition()
                bpartleft = bpad.GetBoundingBox().GetLeft()
                bpartright = bpad.GetBoundingBox().GetRight()
                padwidth = (part.GetBoundingBox().GetRight() - part.GetBoundingBox().GetLeft())/2
                multipart_drift = parts_applied[pad_id] * unscale(300)
                if bpadx > bpartx:
                    direction = 1
                    xpos = bpad.GetBoundingBox().GetRight() + padwidth + unscale(30) + multipart_drift
                    print('right', pad_id, parts_applied[pad_id], multipart_drift)
                else:
                    direction = -1
                    xpos = bpad.GetBoundingBox().GetLeft() - padwidth - unscale(30) - multipart_drift
                    print('left', pad_id, parts_applied[pad_id], -multipart_drift)
                part.SetPosition(pcbnew.VECTOR2I(int(xpos), int(bpady)))

                # try to rotate the part 180 degrees to see if that gets it closer
                distance = abs(pad.GetPosition()[0] - bpad.GetPosition()[0])
                # part.SetOrientationDegrees(180)
                distance2 = abs(pad.GetPosition()[0] - bpad.GetPosition()[0])
                if distance2 > distance:
                    print('~rotated ', part.GetValue(), distance, distance2)
                    part.SetOrientationDegrees(180)
                else:
                    print(' rotated ', part.GetValue(), distance, distance2)
                break
                """
                2. if the pad is connected to a jack, add it to a list of that jack's pin's parts
                2. if the pad is connected to a pot, add it to a list of that pot's pin's parts
                3. if the pad is connected to a chip, add it to a list of that chip's pin's parts
                4. if the pad is connected to a transistor, add it to a list of that transistor's pin's parts
                5. if none of these have happened, try the next pad
                """
        pcbnew.Refresh()
            # 2. if the part has not been assigned to any pin, add it to spare_parts list

        # ics = [ p for p in self.parts if p.name[0] == 'U' ]
        # pads = []
        # for ic in ics:
        #     for pad in ic.pads:
        #         pads.append(pad)

        # exclude_nets = [ 'GND', '+12V', '-12V', '+5V' ]
        # movables = []
        # for p in self.parts:
        #     print(p.name[0])
        #     if p.name[0] not in self.exclude_types:
        #         movables.append(p)

        # for part in movables:
        #     if part.x < 90000000:
        #         continue
        #     print(part.x)
        #     # find a pad that is connected to an IC
        #     connected_pad = None
        #     for pad in part.pads:
        #         if pad.netname in exclude_nets:
        #             continue
        #         netpads = self.nets[pad.netname]
        #         for npad in netpads:
        #             if npad.part.name[0] == 'U':
        #                 connected_pad = npad
        #     if connected_pad == None:
        #         continue
            
        #     # get orientation of pad
        #     conn_orient = 'vert'
        #     if connected_pad.width > connected_pad.height:
        #         conn_orient = 'horiz'

        #     dir_y = 0
        #     dir_x = 0
        #     if conn_orient == 'vert':
        #         dir_y = 1 if connected_pad.y > connected_pad.part.y else -1
        #     else:
        #         dir_x = 1 if connected_pad.x > connected_pad.part.x else -1
        #     part.x = connected_pad.x + dir_x*pad.part.width
        #     part.y = connected_pad.y + dir_y*pad.part.height

        #     pad_orient = 'vert'
        #     if pad.part.width > pad.part.height:
        #         pad_orient = 'horiz'

        #     # print(part.name, '\t', pad.name, '\t', connected_pad.part.name, '\t', connected_pad.name, '\t', pad.netname, '\t', pad.width, '\t', pad.height, '\t', pad_orient, '\t', conn_orient, '\t', dir_x, '\t', dir_y)

        #     if pad_orient != conn_orient:
        #         # rotate 90deg
        #         # print('rotating')
        #         # print(pad.part.angle)
        #         pad.part.angle += math.radians(90)
        #         # print(pad.part.angle)

        # self.update_board()
        # get pins for all ICs
        # get nets for those pins
        # get parts connected to those nets
        # choose the first IC from the list of ICs connected to the net
        # get the x,y position and bounding box of the IC pin
        # set the orietation of the part to be the same orientation as the IC pin, with the pin of the part facing the pin of the IC
        # set the x,y position of the part to be aligned with the pin, 3mm away from the pin

