from flask import Flask, request, render_template
from flask_cors import CORS
import json
import wda
import tidevice
import time
import os
import subprocess
from logzero import logger

app = Flask(__name__, template_folder='static')
CORS(app, support_crenditals=True, resources={r"/*": {"origins": "*"}}, send_wildcard=True)


def _load_device_config():
    config_path = os.path.join(os.path.abspath(''), 'device.json')
    if not os.path.exists(config_path):
        return {}

    with open(config_path, 'r', encoding='utf-8') as fp:
        return json.load(fp)


def _resolve_device_udid():
    config = _load_device_config()
    configured_udid = os.environ.get('IOS_REMOTE_UDID') or config.get('udid', '').strip()
    if configured_udid:
        return configured_udid

    usb_devices = [info for info in tidevice.Usbmux().device_list() if info.conn_type.value == 'usb']
    if len(usb_devices) == 1:
        return usb_devices[0].udid
    if len(usb_devices) == 0:
        raise RuntimeError('No USB device connected')

    device_list = ', '.join(info.udid for info in usb_devices)
    raise RuntimeError(f'Multiple USB devices connected, please configure device.json or IOS_REMOTE_UDID: {device_list}')


def connect_device():
    c = wda.USBClient(udid=device_udid)
    return c


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/remote', methods=['POST'])
def remote():
    data = json.loads(request.form.get('data'))
    content = data['text']
    logger.info('remote to: {}'.format(content))
    subprocess.Popen(cmds['remote'].format(content), shell=True, stdout=subprocess.PIPE).communicate()
    return "remote screen"


@app.route('/click', methods=['POST'])
def click():
    data = json.loads(request.form.get('data'))
    disX = float(data['disX'])
    disY = float(data['disY'])
    client.click(disX, disY)
    logger.info('click: ({}, {})'.format(disX, disY))
    return "click it"


@app.route('/drag', methods=['POST'])
def drag():
    data = json.loads(request.form.get('data'))
    disX = float(data['disX'])
    disY = float(data['disY'])
    toX = float(data['toX'])
    toY = float(data['toY'])
    client.swipe(x1=disX, y1=disY, x2=toX, y2=toY, duration=0)
    logger.info('drag: ({}, {}) and drag to: ({}, {})'.format(disX, disY, toX, toY))
    return "click and drag it"


@app.route('/home', methods=['POST'])
def home():
    device.instruments.app_launch('com.apple.springboard')
    client.orientation = 'PORTRAIT'
    logger.info('Back to home')
    return "click home button"


@app.route('/backspace', methods=['POST'])
def backspace():
    client.send_keys('\b')
    logger.info('Click backspace')
    return "click backspace"


@app.route('/enter', methods=['POST'])
def enter():
    client.send_keys('\n')
    logger.info('Click enter')
    return "click enter"


@app.route('/lock', methods=['POST'])
def lock():
    client.lock()
    logger.info('Press lock button to lock/unlock')
    return "press lock button"


@app.route('/screenshot', methods=['POST'])
def screenshot():
    screenshot_name = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    device.screenshot().convert("RGB").save(f'{path}/screenshot/{screenshot_name}.png')
    # os.system(f'tidevice screenshot {path}/screenshot/{screenshot_name}.png')
    logger.info('Press screenshot button to screenshot')
    return "press screenshot button"


@app.route('/rotation', methods=['POST'])
def rotation():
    orientation = client.orientation
    if orientation == 'PORTRAIT':
        client.orientation = 'LANDSCAPE'
    else:
        client.orientation = 'PORTRAIT'
    logger.info('Switch orientation')
    return "switch orientation"


@app.route('/reboot', methods=['POST'])
def reboot():
    device.reboot()
    logger.info('Press reboot button to reboot')
    return "press reboot button"


@app.route('/send', methods=['POST'])
def send():
    data = json.loads(request.form.get('data'))
    content = data['text']
    client.send_keys(content)
    logger.info('send text content: {}'.format(content))
    return "send text"


if __name__ == '__main__':
    path = os.path.abspath('')
    device_udid = _resolve_device_udid()
    cmds = {'remote': f'tidevice -u {device_udid} relay {{0}} 9100'}
    device = tidevice.Device(device_udid)
    client = connect_device()
    app.run(debug=True)
