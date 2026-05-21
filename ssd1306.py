import time
from machine import Pin

# MicroPython SSD1306 OLED driver, I2C and SPI interfaces
SET_CONTRAST = const(0x81)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_SCAN_DIR = const(0xC0)
SET_SEG_REMAP = const(0xA0)
SET_CHARGE_PUMP = const(0x8D)
SET_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_COM_PIN_CFG = const(0xDA)

class SSD1306(object):
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        self.init_display()

    def init_display(self):
        for cmd in (SET_DISP | 0x00, SET_CLK_DIV, 0x80, 0x20, 0x00, 0x21, 0, self.width - 1, 0x22, 0, self.pages - 1, SET_SCAN_DIR | 0x08, 0x40, SET_SEG_REMAP | 0x01, SET_NORM_INV, SET_CONTRAST, 0xCF, SET_CHARGE_PUMP, 0x14, SET_DISP | 0x01):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self): self.write_cmd(SET_DISP | 0x00)
    def poweron(self): self.write_cmd(SET_DISP | 0x01)
    def contrast(self, contrast): self.write_cmd(SET_CONTRAST); self.write_cmd(contrast)
    def invert(self, invert): self.write_cmd(SET_NORM_INV | (invert & 1))
    def show(self): self.write_data(self.buffer)
    def fill(self, col):
        for i in range(len(self.buffer)): self.buffer[i] = 0xFF if col else 0x00
    def pixel(self, x, y, col):
        if 0 <= x < self.width and 0 <= y < self.height:
            index = (y // 8) * self.width + x
            offset = y % 8
            if col: self.buffer[index] |= (1 << offset)
            else: self.buffer[index] &= ~(1 << offset)
    def scroll(self, dx, dy): pass
    def text(self, string, x, y, col=1):
        import framebuf
        fbuf = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        fbuf.text(string, x, y, col)

class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b'\x40', None]
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x00
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)