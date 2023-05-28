#!/usr/bin/python

from enum import Enum
import shutil
import os
import argparse

import ETXinitPassthrough
import serials_find
import upload_via_esp8266_backpack

import sys
from os.path import dirname

sys.path.append(dirname(__file__) + '/external/esptool')
from external.esptool import esptool


class ElrsUploadResult:
    # SUCCESS
    Success = 0
    # ERROR: Unspecified
    ErrorGeneral = -1
    # ERROR: target mismatch
    ErrorMismatch = -2

class DeviceType(Enum):
    VRX = 'vrx'
    TXBP = 'txbp'
    def __str__(self):
        return self.value

class MCUType(Enum):
    ESP8266 = 'esp8266'
    ESP32 = 'esp32'
    def __str__(self):
        return self.value

class UploadMethod(Enum):
    uart = 'uart'
    passthru = 'passthru'
    edgetx = 'edgetx'
    wifi = 'wifi'
    dir = 'dir'
    def __str__(self):
        return self.value

def upload_wifi(args, mcuType, upload_addr, isstm: bool):
    wifi_mode = 'upload'
    if args.force == True:
        wifi_mode = 'uploadforce'
    elif args.confirm == True:
        wifi_mode = 'uploadconfirm'
    if args.port:
        upload_addr = [args.port]
    if mcuType == MCUType.ESP8266:
        return upload_via_esp8266_backpack.do_upload('firmware.bin.gz', wifi_mode, upload_addr, isstm, {})
    else:
        return upload_via_esp8266_backpack.do_upload(args.file.name, wifi_mode, upload_addr, isstm, {})

def upload_esp8266_uart(args):
    if args.port == None:
        args.port = serials_find.get_serial_port()
    try:
        esptool.main(['--chip', 'esp8266', '--port', args.port, '--baud', str(args.baud), '--after', 'soft_reset', 'write_flash', '0x0000', args.file.name])
    except:
        return ElrsUploadResult.ErrorGeneral
    return ElrsUploadResult.Success

def upload_esp8266_etx(args):
    if args.port == None:
        args.port = serials_find.get_serial_port()
    ETXinitPassthrough.etx_passthrough_init(args.port, 460800)
    try:
        esptool.main(['--passthrough', '--chip', 'esp8266', '--port', args.port, '--baud', '460800', '--before', 'no_reset', '--after', 'soft_reset', 'write_flash', '0x0000', args.file.name])
    except:
        return ElrsUploadResult.ErrorGeneral
    return ElrsUploadResult.Success

def upload_esp8266_passthru(args):
    if args.port == None:
        args.port = serials_find.get_serial_port()
    try:
        esptool.main(['--passthrough', '--chip', 'esp8266', '--port', args.port, '--baud', '230400', '--before', 'passthru', '--after', 'soft_reset', 'write_flash', '0x0000', args.file.name])
    except:
        return ElrsUploadResult.ErrorGeneral
    return ElrsUploadResult.Success

def upload_esp32_uart(args):
    if args.port == None:
        args.port = serials_find.get_serial_port()
    try:
        dir = os.path.dirname(args.file.name)
        esptool.main(['--chip', 'esp32', '--port', args.port, '--baud', str(args.baud), '--after', 'hard_reset', 'write_flash', '-z', '--flash_mode', 'dio', '--flash_freq', '40m', '--flash_size', 'detect', '0x1000', os.path.join(dir, 'bootloader.bin'), '0x8000', os.path.join(dir, 'partitions.bin'), '0xe000', os.path.join(dir, 'boot_app0.bin'), '0x10000', args.file.name])
    except:
        return ElrsUploadResult.ErrorGeneral
    return ElrsUploadResult.Success

def upload_esp32_etx(args):
    if args.port == None:
        args.port = serials_find.get_serial_port()
    ETXinitPassthrough.etx_passthrough_init(args.port, 460800)
    try:
        dir = os.path.dirname(args.file.name)
        esptool.main(['--passthrough', '--chip', 'esp32', '--port', args.port, '--baud', '460800', '--before', 'no_reset', '--after', 'hard_reset', 'write_flash', '-z', '--flash_mode', 'dio', '--flash_freq', '40m', '--flash_size', 'detect', '0x1000', os.path.join(dir, 'bootloader.bin'), '0x8000', os.path.join(dir, 'partitions.bin'), '0xe000', os.path.join(dir, 'boot_app0.bin'), '0x10000', args.file.name])
    except:
        return ElrsUploadResult.ErrorGeneral
    return ElrsUploadResult.Success

def upload_esp32_passthru(args):
    if args.port == None:
        args.port = serials_find.get_serial_port()
    try:
        dir = os.path.dirname(args.file.name)
        esptool.main(['--passthrough', '--chip', 'esp32', '--port', args.port, '--baud', '230400', '--before', 'passthru', '--after', 'hard_reset', 'write_flash', '-z', '--flash_mode', 'dio', '--flash_freq', '40m', '--flash_size', 'detect', '0x1000', os.path.join(dir, 'bootloader.bin'), '0x8000', os.path.join(dir, 'partitions.bin'), '0xe000', os.path.join(dir, 'boot_app0.bin'), '0x10000', args.file.name])
    except:
        return ElrsUploadResult.ErrorGeneral
    return ElrsUploadResult.Success

def upload_dir(mcuType, args):
    if mcuType == MCUType.ESP8266:
        shutil.copy2(args.file.name, args.out)
    elif mcuType == MCUType.ESP32:
        dir = os.path.dirname(args.file.name)
        shutil.copy2(args.file.name, args.out)
        shutil.copy2(os.path.join(dir, 'bootloader.bin'), args.out)
        shutil.copy2(os.path.join(dir, 'partitions.bin'), args.out)
        shutil.copy2(os.path.join(dir, 'boot_app0.bin'), args.out)

def upload(deviceType: DeviceType, mcuType: MCUType, args):
    if args.baud == 0:
        args.baud = 460800

    if args.flash == UploadMethod.dir:
        return upload_dir(mcuType, args)
    elif deviceType == DeviceType.VRX:
        if mcuType == MCUType.ESP8266:
            if args.flash == UploadMethod.uart:
                return upload_esp8266_uart(args)
            elif args.flash == UploadMethod.wifi:
                return upload_wifi(args, mcuType, ['elrs_vrx', 'elrs_vrx.local'], False)
        elif mcuType == MCUType.ESP32:
            if args.flash == UploadMethod.uart:
                return upload_esp32_uart(args)
            elif args.flash == UploadMethod.wifi:
                return upload_wifi(args, mcuType, ['elrs_vrx', 'elrs_vrx.local'], False)
    else:
        if mcuType == MCUType.ESP8266:
            if args.flash == UploadMethod.edgetx:
                return upload_esp8266_etx(args)
            elif args.flash == UploadMethod.uart:
                return upload_esp8266_uart(args)
            elif args.flash == UploadMethod.passthru:
                return upload_esp8266_passthru(args)
            elif args.flash == UploadMethod.wifi:
                return upload_wifi(args, mcuType, ['elrs_txbp', 'elrs_txbp.local'], False)
        if mcuType == MCUType.ESP32:
            if args.flash == UploadMethod.edgetx:
                return upload_esp32_etx(args)
            elif args.flash == UploadMethod.uart:
                return upload_esp32_uart(args)
            elif args.flash == UploadMethod.passthru:
                return upload_esp32_passthru(args)
            elif args.flash == UploadMethod.wifi:
                return upload_wifi(args, mcuType, ['elrs_txbp', 'elrs_txbp.local'], False)
    print("Invalid upload method for firmware")
    return ElrsUploadResult.ErrorGeneral

def length_check(l, f):
    def x(s):
        if (len(s) > l):
            raise argparse.ArgumentTypeError(f'too long, {l} chars max')
        else:
            return s
    return x

class readable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir=values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))

class writeable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir=values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.W_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a writeable dir".format(prospective_dir))

def main():
    parser = argparse.ArgumentParser(description="Flash Binary Firmware")
    # firmware/targets directory
    parser.add_argument('--dir', action=readable_dir, default=None)
    # Bind phrase
    parser.add_argument('--phrase', type=str, help='Your personal binding phrase')
    # WiFi Params
    parser.add_argument('--ssid', type=length_check(32, "ssid"), required=False, help='Home network SSID')
    parser.add_argument('--password', type=length_check(64, "password"), required=False, help='Home network password')
    parser.add_argument('--auto-wifi', type=int, help='Interval (in seconds) before WiFi auto starts, if no connection is made')
    parser.add_argument('--no-auto-wifi', action='store_true', help='Disables WiFi auto start if no connection is made')
    # Unified target
    parser.add_argument('--target', type=str, help='Unified target JSON path')
    # Flashing options
    parser.add_argument("--flash", type=UploadMethod, choices=list(UploadMethod), help="Flashing Method")
    parser.add_argument('--out', action=writeable_dir, default=None)
    parser.add_argument("--port", type=str, help="SerialPort or WiFi address to flash firmware to")
    parser.add_argument("--baud", type=int, default=0, help="Baud rate for serial communication")
    parser.add_argument("--force", action='store_true', default=False, help="Force upload even if target does not match")
    parser.add_argument("--confirm", action='store_true', default=False, help="Confirm upload if a mismatched target was previously uploaded")
    # Firmware file to patch/configure
    parser.add_argument("file", nargs="?", type=argparse.FileType("r+b"))

    args = parser.parse_args()

    type = args.target.split('.')[0]
    if type == 'txbp':
        mcu = MCUType.ESP8266
    else:
        mcu = args.target.split('.')[2]
        if mcu == 'esp32': mcu = MCUType.ESP32
        else: mcu = MCUType.ESP8266
    print (type, mcu)

    upload(DeviceType.TXBP if type == 'txbp' else DeviceType.VRX, mcu, args)

if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(e)
        exit(1)