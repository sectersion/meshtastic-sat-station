from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from pathlib import Path

mesh_path = Path("/dev/ttyUSB0")


serial = i2c(port=1, address=0x00) ##replace with actual i2c address when i finish
device = ssd1306(serial)

with canvas(device) as draw:
    if mesh_path.is_file():
        draw.text((0,0), "Node Linked", fill=255)
    else:
        draw.text((0,0), "Node Missing", fill=255)