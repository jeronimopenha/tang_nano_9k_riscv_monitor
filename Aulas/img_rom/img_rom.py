from PIL import Image
from math import ceil, log2

im = Image.open("/home/jeronimo/Documentos/GIT/tang_nano_9k_riscv_monitor/teste_.bmp")
im.load()
height, widht = im.size
p = []
for row in range(height):
    for col in range(widht):
        a = im.getpixel((row, col))
        nr = int(a[0]/255*32)
        ng = int(a[0]/255*64)
        nb = int(a[0]/255*32)
        hex = (nr << 11) | (ng << 5) | nr
        p.append("%0.4X\n" % (hex))
pot_2 = ceil(log2(len(p)))
diff = pow(2, pot_2) - len(p)
for i in range(diff):
    p.append("%0.4X\n" % (0))
counter = 0
with open('/home/jeronimo/Documentos/GIT/tang_nano_9k_riscv_monitor/arch.rom', 'w') as file:
    #for v in p:
    file.writelines(p)
    #file.writelines("assign pixel[%d] = 16'h%s;\n" % (counter, v))
    #counter += 1

file.close()
