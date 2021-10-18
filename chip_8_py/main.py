'''
Ref:
https://github.com/mattmikolay/chip-8/wiki/CHIP%E2%80%908-Technical-Reference
https://en.wikipedia.org/wiki/CHIP-8
'''

import sys
import sdl2
import sdl2.ext

BLACK = sdl2.ext.Color(0, 0, 0)
WHITE = sdl2.ext.Color(255, 255, 255)

# big endian integer from nibs
def be(*nibs):
    a = 0
    for n in nibs:
        a = a * 16 + n
    return a

class Chip8:


    def __init__(self, memsize=4096) -> None:
        # 1 byte per element
        self.memory = [0] * memsize
        # 1 byte per reg: V0-VF
        self.v = [0] * 16
        # reg I
        self.i = 0
        # stack for subroutines
        self.stack  = []
        # sound timer
        self.sound_timer = 0
        # delay timer
        self.delay_timer = 0

        self.h = 32
        self.w = 64
        self.screen = [[0] * self.w for _ in range(self.h)]
        scale = 8
        
        sdl2.ext.init()
        self.window = sdl2.ext.Window("chip-8", size=(self.w * scale, self.h * scale))
        self.renderer = sdl2.ext.Renderer(self.window)
        self.renderer.scale = (scale, scale)
        self.ip = 0x200

    def load(self, program):
        # :0x200+len(program)
        self.memory[0x200: ] = program

    # run 1k instructions
    def run_tick(self) -> None:
        count = 30
        while 0 <= self.ip < len(self.memory) and count > 0:
            self.execute(self.memory[self.ip:self.ip+2])
            self.ip += 2
            count -= 1

    def set_pixel(self, x, y, on):
        ret = +(not on and self.screen[y][x])
        self.screen[y][x] = on
        self.renderer.draw_point([x, y], 0xff00ff00 if on else 0)
        return ret

    def clear_screen(self):
        self.screen = [[0] * self.w for _ in range(self.h)]
        self.renderer.clear()
    
    def run(self) -> None:
        self.window.show()
        running = True
        while running:
            self.run_tick()
            for event in sdl2.ext.get_events():
                if event.type == sdl2.SDL_QUIT:
                    running = False
                    break
            sdl2.SDL_Delay(100)
            self.renderer.present()

    def execute(self, inst) -> None:
        nibs = [(inst[0] >> 4) & 0xf, inst[0] & 0xf, (inst[1] >> 4) & 0xf, inst[1] & 0xf]
        print(f'{inst[0] * 256 + inst[1]:04x} {self.ip:08x} {[f"{x:02x}" for x in self.v]} {self.i:08x}')
        match nibs:
            case [0, 0, 0xe, 0]:
                # 00E0: Clears the screen.
                self.clear_screen()
            case [1, n2, n1, n0]:
                # 1NNN: Jumps to address NNN.
                self.ip = be(n2, n1, n0) - 2
            case [2, n2, n1, n0]:
                # 2NNN: Calls subroutine at NNN.
                self.stack.append(self.ip)
                self.ip = be(n2, n1, n0) - 2
            case [0x6, x, n1, n0]:
                # 6XNN: Sets VX to NN.
                self.v[x] = be(n1, n0)
            case [0x7, x, n1, n0]:
                # 7XNN: Adds NN to VX. (Carry flag is not changed)
                self.v[x] += be(n1, n0)
            case [0xa, n2, n1, n0]:
                # ANNN: Sets I to the address NNN.
                self.i = be(n2, n1, n0)
            case [0xd, x, y, n]:
                # DXYN: Draws a sprite at coordinate (VX, VY)
                # that has a width of 8 pixels and a height of N pixels. 
                # Each row of 8 pixels is read as bit-coded starting from memory location I; 
                # I value does not change after the execution of this instruction. 
                # As described above, VF is set to 1 if any screen pixels are flipped from 
                # set to unset when the sprite is drawn, and to 0 if that does not happen
                self.v[0xf] = 0 + any(
                    self.set_pixel(self.v[x] + j, self.v[y] + i, self.memory[self.i + i] >> (7 - j) & 1)
                    for j in range(8) for i in range(n)
                )
            case [n3, n2, n1, n0]:
                raise NotImplementedError(f"unknown inst: {be(n3, n2, n1, n0):04x}")


c = Chip8()
with open(sys.argv[1], 'rb') as f:
    c.load(f.read())
c.run()







# class SoftwareRenderSystem(sdl2.ext.SoftwareSpriteRenderSystem):
#     def __init__(self, window):
#         super(SoftwareRenderSystem, self).__init__(window)

#     def render(self, components):
#         sdl2.ext.fill(self.surface, BLACK)
#         super(SoftwareRenderSystem, self).render(components)


# class TextureRenderSystem(sdl2.ext.TextureSpriteRenderSystem):
#     def __init__(self, renderer):
#         super(TextureRenderSystem, self).__init__(renderer)
#         self.renderer = renderer

#     def render(self, components):
#         tmp = self.renderer.color
#         self.renderer.color = BLACK
#         self.renderer.clear()
#         self.renderer.color = tmp
#         super(TextureRenderSystem, self).render(components)

# def run():
#     sdl2.ext.init()
#     window = sdl2.ext.Window("The Pong Game", size=(800, 600))
#     window.show()

#     if "-hardware" in sys.argv:
#         print("Using hardware acceleration")
#         renderer = sdl2.ext.Renderer(window)
#         factory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=renderer)
#     else:
#         print("Using software rendering")
#         factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)

#     if factory.sprite_type == sdl2.ext.SOFTWARE:
#         spriterenderer = SoftwareRenderSystem(window)
#     else:
#         spriterenderer = TextureRenderSystem(renderer)

#     screen = factory.from_color(WHITE, (512, 256))
#     for i in range(10):
#         sdl2.ext.PixelView(screen)[10][10+i] = 0xffff0000
#     print(hex(sdl2.ext.PixelView(screen)[10][10]))
    
#     running = True
#     while running:
#         for event in sdl2.ext.get_events():
#             if event.type == sdl2.SDL_QUIT:
#                 running = False
#                 break
#         sdl2.SDL_Delay(16)
#         spriterenderer.render(screen)


# if __name__ == "__main__":
#     sys.exit(run())