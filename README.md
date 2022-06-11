Kicad-Eurorack-Tools
====================

This project provides 3 main things to facilitate designing your own analog synthesizer modules in the Eurorack format:

1. The `EuroRackTools` parts library. This is an *atomic* parts library. Each schematic symbol is pre-assigned a footprint and LCSC part number.
2. The `EuroRack Tools` pcbnew python plugin. This plugin will draw a eurorack-spec'd cutout with ground flood planes. The pre-drawn cutout is the size of a frontpanel and has perforation cuts on the top and bottom so you can snap them off and create a real faceplate. A second button is provided that will create that faceplate, with holes properly aligned for Alpha pots and Thonkiconn jacks mounting, and holes for LEDs.
3. The `kicad-eurorack-simulation.lib` simulation file.


Installation
------------

I'm still working this out.

Open KiCad version 6.0 or later.

1. Click the `Plugin and Content Manager` button.
2. Click the `Manage` button next to the repository list dropdown.
3. Click the `+` button on the bottom left, and enter https://github.com/danroblewis/kicad-eurorack-tools/raw/master/packaging/repository.json
4. Click `Save`
5. Then you have to select `danroblew's KiCad repository` from the repository list dropdown.
6. Click `Install`, then `Apply Changes` and it'll download!




Plugin
------

After installing the plugin, a new plugin button should appear in the upper right. Enter the width of your intended module (in HP dimensions), and click `Draw Panel`.

Then lay out your parts in the board, draw your traces, run your checks, etc.

When you've done with your backpanel, click the plugin button again and click `Draw Frontpanel`.


Library
-------

When designing your circuits, try to limit yourself to components in this library. 


Simulation
----------

To set up a simluation:

1. Add 2 `VSOURCE` symbols. Give them the value `dc 12`
2. Add 1 `VSOURCE` symbol with the value `dc 5`
3. Connect the 12v `VSOURCE` symbols together. Their center point is ground. Connect the 5v `VSOURCE` symbol to this ground.
4. Add `GND` to the middle point, add a `+12V` symbol to the top, add `-12V` to the bottom, and add `+5V` to your 5v `VSOURCE`
5. Add a new text element to your schematic with the following text:
```spice
.tran 1m 1
.include "C:\Users\<yourname>\Downloads\kicad-eurorack-simulation.lib"
```
6. Click `Inspect` in the top bar, `Simulator...` from the menu, click `Run/Stop Simulation`, then click `Probe` and choose a trace you want to inspect.

