#! /usr/bin/env python3
import os
import sys
from PIL import Image, ImageDraw
from subprocess import Popen, PIPE

def create_image(w, h, result):
    cd = os.path.abspath(os.path.dirname(__file__))
    cv = Image.new("RGB", (w, h))
    circle = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(circle)
    s, *v = [int(x) for x in result.split()]
    for i in range(s // 4):
        i *= 4
        y, x, d, c = v[i:i+4]
        r, g, b = c>>16, (c>>8)&0xff, c&0xff
        draw.ellipse((x-d, y-d, x+d, y+d), fill=(r, g, b))
        cv = Image.blend(cv, circle, 0.5).convert("RGB")
        circle = cv.copy()
        draw = ImageDraw.Draw(circle)
    cv.save(cd + '/' + 'circlesmix.png')

def create_input(n):
    cd = os.path.abspath(os.path.dirname(__file__))
    image = Image.open(cd + '/' + 'image', 'r')
    w, h = image.size
    if w > 800:
        h = int(h * (800 / w))
        w = 800
    if h > 800:
        w = int(h * (800 / h))
        h = 800
    image = image.resize((w, h))
    datas = [str(h), str(h*w)]
    for y in range(h):
        for x in range(w):
            r, g, b = image.getpixel((x, y))
            datas += [str((r << 16) + (g << 8) + b)]
    return w, h, '\n'.join(datas + [str(n)])

def run_circlesmix(_input):
    cd = os.path.abspath(os.path.dirname(__file__))
    _input_encode = _input.encode('utf-8')
    p = Popen(cd + '/' + 'CirclesMix.exe', stdout=PIPE, stdin=PIPE, stderr=PIPE)
    result = ''
    try:
        t = p.communicate(input=_input_encode)
        out = t[0].decode('utf-8').replace('\r\n', '\n')
        err = t[1].decode('utf-8').replace('\r\n', '\n')
        result = out
    except:
        p.kill()
        p.wait()
    return result

def main():
    n = 1000
    if len(sys.argv) > 1 : n = int(sys.argv[1])
    print('circlesmix.py %d' % n)
    w, h, _input = create_input(n)
    result = run_circlesmix(_input)
    if result : create_image(w, h, result)

if __name__ == '__main__':
    main()
