import makerbot_driver, serial, sys, threading, time

def render_line(start, end, length):
    return [ 1 if i >= start and i <= end else 0 for i in xrange(length)]

def render_frame(width, height, scale):
    frame = []
    for line in range(height):
        distance_to_mid = scale * height - abs(line - height/2)
        start = (0.75 * width) - (width * distance_to_mid / height)
        end = (0.25 * width) + (width * distance_to_mid / height)
        data = render_line(start, end, width)
        print "".join(map(str, data))
        frame.append(data)
    return frame

class Converter:
    def __init__(self):
        self.base_x = 1000
        self.base_y = 1000
        self.base_z = 0
        self.a = 0
        self.b = 0
        self.increment_x = 10
        self.increment_y = 10
        self.fast_speed = 400
        self.slow_speed = 2500
        self.increment_a = -200

    def frame_to_commands(self, frame):
        self.base_z += 30
        commands = []
        for y, line in enumerate(frame):
            last_pixel = 0
            pos_x = self.base_x
            pos_y = self.base_y + self.increment_y * y
            pos_z = 500
            speed = self.fast_speed
            commands.append([pos_x, pos_y, pos_z, self.b, self.a, speed])
            for x, pixel in enumerate(line):
                if pixel == 1 and last_pixel == 0:
                    pos_z = self.base_z
                    # move twice
                    commands.append([pos_x, pos_y, pos_z, self.b, self.a, self.fast_speed])
                    speed = self.slow_speed
                    self.a += self.increment_a
                elif pixel == 1 and last_pixel == 1:
                    self.a += self.increment_a
                else:
                    speed = self.fast_speed
                    pos_z = 5000
                commands.append([pos_x, pos_y, pos_z, self.b, self.a, speed])
                pos_x += self.increment_x
        return commands



class Printer:
    def __init__(self):
        self.r = makerbot_driver.s3g()
        file = serial.Serial("/dev/cu.usbmodem641", 115200, timeout=1)
        self.r.writer = makerbot_driver.Writer.StreamWriter(file, threading.Condition())
        self.r.find_axes_maximums(['x', 'y'], 500, 60)
        self.r.find_axes_minimums(['z'], 500, 60)
        self.r.recall_home_positions(['x', 'y', 'z', 'a', 'b'])

    def run(self, commands):
        print "execute ", len(commands), "commands"
        commands.reverse()
        while(len(commands) > 0):
            try:
                next_command = commands.pop()
                coords = next_command[:-1]
                speed = next_command[-1]
                self.r.queue_extended_point(coords, speed, 0, 0)
                print "coords:", coords, "speed:", speed
            except makerbot_driver.BufferOverflowError:
                print >>sys.stderr, "buffer overflow.. sleeping"
                time.sleep(1.0)


print "rasterizing image"
frames = []
scale = 0.7
while scale >= 0.25:
    frames.append(render_frame(10,18, scale))
    scale -= 0.02
print "printer conversion of", len(frames), "frames"
converter = Converter()
commands = []
for i, frame in enumerate(frames):
    commands += converter.frame_to_commands(frame)
print "printing"
printer = Printer()
printer.run(commands)

