import os

from pcbnew import ActionPlugin

import wx

from .dialog import EurorackTools


class EurorackToolsPlugin(ActionPlugin):
    def defaults(self):
        self.name = "Eurorack Tools"
        self.category = "Fabrication data generation"
        self.description = (
            "Generate Eurorack-compatible Gerber, Excellon, BOM and CPL files"
        )
        self.show_toolbar_button = True
        path, filename = os.path.split(os.path.abspath(__file__))
        self.icon_file_name = os.path.join(path, "jlcpcb-icon.png")
        self._pcbnew_frame = None

    def Run(self):
        dialog = 5
        dialog = EurorackTools(None)
        dialog.Center()
        dialog.Show()



EurorackToolsPlugin().register()
