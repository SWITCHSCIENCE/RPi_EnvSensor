#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import quick2wire.i2c as i2c

class I2Clcd:
	ADDR = 0x3E

	def __init__(self):
		self.bus = i2c.I2CMaster()
		self.contrast = 35

		com1 = (0x38, 0x39, 0x14, 0x70 | (self.contrast & 0x0F), 0x54 | ((self.contrast & 0x30) >> 4), 0x6C)
		self.bus.transaction(i2c.writing_bytes(self.ADDR, *com1))
		time.sleep(0.2)
		com2 = (0x38, 0x0C, 0x01)
		self.bus.transaction(i2c.writing_bytes(self.ADDR, *com2))
		time.sleep(0.002)

	def clear_display(self):
		self.bus.transaction(i2c.writing_bytes(self.ADDR, 0x00, 0x01))

	def set_cursor(self, x, y):
		self.bus.transaction(i2c.writing_bytes(self.ADDR, 0x00, 0x80 | (y * 0x40 + x)))

	def print_dec(self, val, col):
		if col > 8:
			col = 8
		elif col < 1:
			col = 1
		buff = [0, 0, 0, 0, 0, 0, 0, 0]
		for i in range(7, -1, -1):
			buff[i] = val % 10 + 0x30
			val = val // 10
		num_list = buff[8 - col: 8]
		self.bus.transaction(i2c.writing_bytes(self.ADDR, 0x40, *num_list))

	def print_hex(self, val, col):
		if col > 8:
			col = 8
		elif col < 1:
			col = 1
		buff = [0, 0, 0, 0, 0, 0, 0, 0]
		for i in range(7, -1, -1):
			buff[i] = val & 0x0000000F
			val = val >> 4
			if buff[i] > 9:
				buff[i] = buff[i] + 0x37
			else:
				buff[i] = buff[i] + 0x30
		num_list = buff[8 - col: 8]
		self.bus.transaction(i2c.writing_bytes(self.ADDR, 0x40, *num_list))

	def print_str(self, msg_str):
		msg_list = map(ord, list(msg_str))
		self.bus.transaction(i2c.writing_bytes(self.ADDR, 0x40, *msg_list))

class HTU21D:
	ADDR = 0x40
	CMD_READ_TEMP_HOLD = 0xE3
	CMD_READ_HUM_HOLD = 0xE5
	CMD_READ_TEMP_NOHOLD = 0xF3
	CMD_READ_HUM_NOHOLD = 0xF5
	CMD_WRITE_USER_REG = 0xE6
	CMD_READ_USER_REG = 0xE7
	CMD_SOFT_RESET = 0xFE

	def __init__(self):
		self.bus = i2c.I2CMaster()

	def check_crc(self, rawdat):
		for i in range(16):
			rawdat <<= 1
			if rawdat & 0x01000000:
				rawdat ^= 0x01310000
		if rawdat:
			raise CRCFailed("CRC checksum failed.")

	def get_temp(self):
		self.bus.transaction(i2c.writing_bytes(self.ADDR, self.CMD_READ_TEMP_NOHOLD))
		time.sleep(.05)
		results = self.bus.transaction(i2c.reading(self.ADDR, 3))

		raw_temp = int.from_bytes(results[0], byteorder="big")
		self.check_crc(raw_temp)
		return -46.85 + (175.72 * ((raw_temp >> 8) / float(2**16)))

	def get_humidity(self):
		self.bus.transaction(i2c.writing_bytes(self.ADDR, self.CMD_READ_HUM_NOHOLD))
		time.sleep(.05)
		results = self.bus.transaction(i2c.reading(self.ADDR, 3))

		raw_hum = int.from_bytes(results[0], byteorder="big")
		self.check_crc(raw_hum)
		return -6 + (125 * ((raw_hum >> 8) / float(2**16)))

class MPL3115A2:
	ADDR = 0x60
	CMD_OUT_P_MSB = 0x01
	CMD_OUT_P_CSB = 0x02
	CMD_OUT_P_LSB = 0x03
	CMD_OUT_T_MSB = 0x04
	CMD_OUT_T_LSB = 0x05
	CMD_CTRL_REG1 = 0x26
	CMD_CTRL_REG2 = 0x27
	CMD_CTRL_REG3 = 0x28
	CMD_CTRL_REG4 = 0x29
	CMD_CTRL_REG5 = 0x2A

	def __init__(self):
		self.bus = i2c.I2CMaster()

	def write_reg(self, adr, dat):
		self.bus.transaction(i2c.writing_bytes(self.ADDR, adr, dat))

	def read_reg(self, com):
		self.bus.transaction(i2c.writing_bytes(self.ADDR, com))
		results = self.bus.transaction(i2c.reading(self.ADDR, 1))
		return int.from_bytes(results[0], byteorder="big")

	def toggle_one_shot(self):
		dat = self.read_reg(self.CMD_CTRL_REG1)
		dat |= 0x02
		self.write_reg(self. CMD_CTRL_REG1, dat)

		dat = self.read_reg(self.CMD_CTRL_REG1)
		dat &= ~0x02
		self.write_reg(self. CMD_CTRL_REG1, dat)

	def get_pressure(self):
		self.toggle_one_shot()
		time.sleep(.06)

		self.bus.transaction(i2c.writing_bytes(self.ADDR, self.CMD_OUT_P_MSB))
		results = self.bus.transaction(i2c.reading(self.ADDR, 4))

		raw_temp = int.from_bytes(results[0], byteorder="big")
		return (raw_temp >> 4) 

class ATTiny:
	ADDR = 0x6A
	CMD_PORT_LOW = 0x80
	CMD_PORT_HIGH = 0x81
	CMD_AD_READ = 0xC0

	def __init__(self):
		self.bus = i2c.I2CMaster()
		self.pdat = 0

	def port_set(self):
		self.bus.transaction(i2c.writing_bytes(self.ADDR, self.CMD_PORT_HIGH))
		self.pdat = 1

	def port_rst(self):
		self.bus.transaction(i2c.writing_bytes(self.ADDR, self.CMD_PORT_LOW))
		self.pdat = 0

	def port_tgl(self):
		if self.pdat == 0:
			self.bus.transaction(i2c.writing_bytes(self.ADDR, self.CMD_PORT_HIGH))
			self.pdat = 1
		else:
			self.bus.transaction(i2c.writing_bytes(self.ADDR, self.CMD_PORT_LOW))
			self.pdat = 0

	def read_ad(self):
		self.bus.transaction(i2c.writing_bytes(self.ADDR, self.CMD_AD_READ))
		results = self.bus.transaction(i2c.reading(self.ADDR, 1))
		return int.from_bytes(results[0], byteorder="big")

if __name__ == '__main__':
	lcd = I2Clcd()
	sen_light = ATTiny()
	sen_htu = HTU21D()
	sen_mpl = MPL3115A2()

	while 1:
		tdat = sen_htu.get_temp()
		hdat = sen_htu.get_humidity()
		pdat = sen_mpl.get_pressure() / 400
		ldat = sen_light.read_ad()

		print ("tmp : {0:6.2f}  /  hum : {1:6.2f}  /  bar : {2:7.2f}  /  light : {3}".format(tdat, hdat, pdat, ldat))
		lcd.set_cursor(0, 0)
		lcd.print_str('Light:')
		lcd.set_cursor(0, 1)
		lcd.print_dec(ldat, 3)

		sen_light.port_tgl()
		time.sleep(1)
