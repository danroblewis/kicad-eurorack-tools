import datetime
import logging
import os
import re
import sys
import pcbnew

import wx
import wx.dataview
from pcbnew import GetBoard

from .helpers import (
    PLUGIN_PATH,
    GetScaleFactor,
    HighResWxSize,
    get_footprint_by_ref,
    getVersion,
    loadBitmapScaled,
    toggle_exclude_from_bom,
    toggle_exclude_from_pos,
)

from .draw_panel import draw_euro_panel, draw_euro_frontpanel

class EurorackTools(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(
            self,
            parent,
            id=wx.ID_ANY,
            title=f"Eurorack Tools [  ]",
            pos=wx.DefaultPosition,
            size=wx.Size(230, 160),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
        )
        self.window = wx.GetTopLevelParent(self)
        self.SetSize(HighResWxSize(self.window, wx.Size(230, 160)))
        self.scale_factor = GetScaleFactor(self.window)
        self.project_path = os.path.split(GetBoard().GetFileName())[0]
        self.Bind(wx.EVT_CLOSE, self.quit_dialog)
        self.hideref_state = False


        self.hpbox = wx.TextCtrl(
            self,
            wx.ID_ANY,
            "4",
            wx.Point(50,2),
            wx.DefaultSize,
        )

        self.btn_draw_panel = wx.Button(
            self,
            wx.ID_ANY,
            "Draw Panel",
            wx.Point(5,30), # wx.DefaultPosition,
            HighResWxSize(self.window, wx.Size(100, -1)),
            0,
        )

        self.btn_draw_frontpanel = wx.Button(
            self,
            wx.ID_ANY,
            "Draw Frontpanel",
            wx.Point(110,30), # wx.DefaultPosition,
            HighResWxSize(self.window, wx.Size(100, -1)),
            0,
        )

        self.btn_show_autoplacer = wx.Button(
            self,
            wx.ID_ANY,
            "Autoplacer",
            wx.Point(110,60), # wx.DefaultPosition,
            HighResWxSize(self.window, wx.Size(100, -1)),
            0,
        )

        self.btn_show_autoplaceru = wx.Button(
            self,
            wx.ID_ANY,
            "Uplacer",
            wx.Point(10,60), # wx.DefaultPosition,
            HighResWxSize(self.window, wx.Size(100, -1)),
            0,
        )

        self.btn_show_tryplacer = wx.Button(
            self,
            wx.ID_ANY,
            "Tryplacer",
            wx.Point(10,90), # wx.DefaultPosition,
            HighResWxSize(self.window, wx.Size(100, -1)),
            0,
        )

        self.btn_hide_refs = wx.Button(
            self,
            wx.ID_ANY,
            "Hide Refs",
            wx.Point(110,90), # wx.DefaultPosition,
            HighResWxSize(self.window, wx.Size(100, -1)),
            0,
        )

        self.hpbox.Bind(wx.EVT_TEXT_ENTER, self.drawpanel)
        self.btn_draw_panel.Bind(wx.EVT_BUTTON, self.drawpanel)
        self.btn_draw_frontpanel.Bind(wx.EVT_BUTTON, self.drawfrontpanel)
        self.btn_show_autoplacer.Bind(wx.EVT_BUTTON, self.show_autoplacer)
        self.btn_show_autoplaceru.Bind(wx.EVT_BUTTON, self.show_autoplaceru)
        self.btn_show_tryplacer.Bind(wx.EVT_BUTTON, self.show_tryplacer)
        self.btn_hide_refs.Bind(wx.EVT_BUTTON, self.hide_refs)


    def drawpanel(self, e):
        hpwidth = int(self.hpbox.GetValue())
        draw_euro_panel(hpwidth)
        self.quit_dialog(None)

    def drawfrontpanel(self, e):
        hpwidth = int(self.hpbox.GetValue())
        draw_euro_frontpanel(hpwidth)
        self.quit_dialog(None)

    def quit_dialog(self, e):
        """Destroy dialog on close"""
        self.Destroy()
        self.EndModal(0)

    def show_autoplacer(self, e):
        from .autoplace import AutoplacerWindow
        frm = AutoplacerWindow(None, title='Physics Autoplacer')
        frm.Show()

    def show_autoplaceru(self, e):
        from .autoplace_u import AutoplacerUWindow
        frm = AutoplacerUWindow(None, title='IC Based Autoplacer')
        frm.Show()

    def show_tryplacer(self, e):
        from .tryplacer import TryPlacer
        frm = TryPlacer(None, title='Simple Autoplacer')
        frm.Run()

    def hide_refs(self, e):
        fs = pcbnew.GetBoard().GetFootprints()
        self.hideref_state = not self.hideref_state
        for f in fs:
            try:
                r = f.Reference().SetVisible(not self.hideref_state)
            except:
                pass
        pcbnew.Refresh()
