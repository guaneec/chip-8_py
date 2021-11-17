"""
The MIT License (MIT)

Copyright (c) 2021 guaneec

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.




Ref:
https://github.com/mattmikolay/chip-8/wiki/CHIP%E2%80%908-Technical-Reference
https://en.wikipedia.org/wiki/CHIP-8
"""

import sys
import sdl2
import sdl2.ext
from random import randint
from time import time, sleep

FPS = 60

keymap = [
    sdl2.SDLK_x,  # 0
    sdl2.SDLK_1,  # 1
    sdl2.SDLK_2,  # 2
    sdl2.SDLK_3,  # 3
    sdl2.SDLK_q,  # 4
    sdl2.SDLK_w,  # 5
    sdl2.SDLK_e,  # 6
    sdl2.SDLK_a,  # 7
    sdl2.SDLK_s,  # 8
    sdl2.SDLK_d,  # 9
    sdl2.SDLK_z,  # a
    sdl2.SDLK_c,  # b
    sdl2.SDLK_4,  # c
    sdl2.SDLK_r,  # d
    sdl2.SDLK_f,  # e
    sdl2.SDLK_v,  # f
]

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
        font = [
            0xF0,
            0x90,
            0x90,
            0x90,
            0xF0,
            0x20,
            0x60,
            0x20,
            0x20,
            0x70,
            0xF0,
            0x10,
            0xF0,
            0x80,
            0xF0,
            0xF0,
            0x10,
            0xF0,
            0x10,
            0xF0,
            0x90,
            0x90,
            0xF0,
            0x10,
            0x10,
            0xF0,
            0x80,
            0xF0,
            0x10,
            0xF0,
            0xF0,
            0x80,
            0xF0,
            0x90,
            0xF0,
            0xF0,
            0x10,
            0x20,
            0x40,
            0x40,
            0xF0,
            0x90,
            0xF0,
            0x90,
            0xF0,
            0xF0,
            0x90,
            0xF0,
            0x10,
            0xF0,
            0xF0,
            0x90,
            0xF0,
            0x90,
            0x90,
            0xE0,
            0x90,
            0xE0,
            0x90,
            0xE0,
            0xF0,
            0x80,
            0x80,
            0x80,
            0xF0,
            0xE0,
            0x90,
            0x90,
            0x90,
            0xE0,
            0xF0,
            0x80,
            0xF0,
            0x80,
            0xF0,
            0xF0,
            0x80,
            0xF0,
            0x80,
            0x80,
        ]
        self.memory[: len(font)] = font

        # 1 byte per reg: V0-VF
        self.v = [0] * 16
        # reg I
        self.i = 0
        # stack for subroutines
        self.stack = []
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

        self.pressed = [0] * 16
        self.last_pressed = None

    def load(self, program):
        self.memory[0x200 : 0x200 + len(program)] = program

    # run 1k instructions
    def run_tick(self) -> None:
        count = 100
        end = False
        while not end and 0 <= self.ip < len(self.memory) and count > 0:
            end = self.execute(self.memory[self.ip : self.ip + 2])
            self.ip += 2
            count -= 1

    def set_pixel(self, x, y, on):
        if not on or not 0 <= x < self.w or not 0 <= y < self.h:
            return 0
        # print(x, y)
        self.screen[y][x] ^= 1
        self.renderer.draw_point(
            [x, y], 0xFF00FF00 if self.screen[y][x] else 0xFF000000
        )
        return not self.screen[y][x]

    def clear_screen(self):
        self.screen = [[0] * self.w for _ in range(self.h)]
        self.renderer.clear()

    def run(self) -> None:
        self.window.show()
        running = True
        t, f = 0, FPS
        tp = 0
        while running:
            f -= 1
            if f <= 0:
                tt = time()
                print(f"fps: {FPS / (tt - t):.2f}")
                f, t = FPS, tt
            self.run_tick()
            self.delay_timer = max(0, self.delay_timer - 1)
            if self.sound_timer == 1:
                print("TODO: beep")
            self.sound_timer = max(0, self.sound_timer - 1)
            for event in sdl2.ext.get_events():
                if event.type == sdl2.SDL_QUIT:
                    running = False
                    break
                if event.type in (sdl2.SDL_KEYDOWN, sdl2.SDL_KEYUP):
                    try:
                        self.last_pressed = i = keymap.index(event.key.keysym.sym)
                        self.pressed[i] = +(event.type == sdl2.SDL_KEYDOWN)
                    except ValueError:
                        pass
            tn = time()
            while time() - tp < 1 / FPS:
                sleep(time() - tp)
            tp = tn
            self.renderer.present()

    def execute(self, inst) -> bool:
        nibs = [
            (inst[0] >> 4) & 0xF,
            inst[0] & 0xF,
            (inst[1] >> 4) & 0xF,
            inst[1] & 0xF,
        ]
        # print(f'{inst[0] * 256 + inst[1]:04x} {self.ip:08x} {[f"{x:02x}" for x in self.v]} {self.i:08x}')
        end = False
        match nibs:
            case [0, 0, 0xE, 0]:
                # 00E0: Clears the screen.
                self.clear_screen()
            case [0, 0, 0xE, 0xE]:
                # 00EE: Returns from a subroutine.
                self.ip = self.stack.pop()
            case [1, n2, n1, n0]:
                # 1NNN: Jumps to address NNN.
                self.ip = be(n2, n1, n0) - 2
            case [2, n2, n1, n0]:
                # 2NNN: Calls subroutine at NNN.
                self.stack.append(self.ip)
                self.ip = be(n2, n1, n0) - 2
            case [0x3, x, n1, n0]:
                # 3XNN: Skips the next instruction if VX equals NN. (Usually the next instruction is a jump to skip a code block)
                if self.v[x] == be(n1, n0):
                    self.ip += 2
            case [0x4, x, n1, n0]:
                # 4XNN: Skips the next instruction if VX does not equal NN. (Usually the next instruction is a jump to skip a code block)
                if self.v[x] != be(n1, n0):
                    self.ip += 2
            case [0x5, x, y, 0x0]:
                # 5XY0: Skips the next instruction if VX equals VY. (Usually the next instruction is a jump to skip a code block);
                if self.v[x] == self.v[y]:
                    self.ip += 2
            case [0x6, x, n1, n0]:
                # 6XNN: Sets VX to NN.
                self.v[x] = be(n1, n0)
            case [0x7, x, n1, n0]:
                # 7XNN: Adds NN to VX. (Carry flag is not changed)
                self.v[x] = self.v[x] + be(n1, n0) & 0xFF
            case [0x8, x, y, 0x0]:
                # 8XY0: Sets VX to the value of VY.
                self.v[x] = self.v[y]
            case [0x8, x, y, 0x1]:
                # 8XY1: Sets VX to VX or VY. (Bitwise OR operation);
                self.v[x] |= self.v[y]
            case [0x8, x, y, 0x2]:
                # 8XY2: Sets VX to VX and VY. (Bitwise AND operation);
                self.v[x] &= self.v[y]
            case [0x8, x, y, 0x3]:
                # 8XY3: Sets VX to VX xor VY.
                self.v[x] ^= self.v[y]
            case [0x8, x, y, 0x4]:
                # 8XY4: Adds VY to VX. VF is set to 1 when there's a carry, and to 0 when there is not.
                self.v[x] += self.v[y]
                self.v[0xF] = self.v[x] >> 8
                self.v[x] &= 0xFF
            case [0x8, x, y, 0x5]:
                # 8XY5: VY is subtracted from VX. VF is set to 0 when there's a borrow, and 1 when there is not.
                self.v[x] -= self.v[y]
                self.v[0xF] = self.v[x] >= 0
                self.v[x] += 0x100 * (self.v[x] < 0)
            case [0x8, x, y, 0x6]:
                # 8XY6: Stores the least significant bit of VX in VF and then shifts VX to the right by 1.
                self.v[0xF] = self.v[x] & 1
                self.v[x] >>= 1
            case [0x8, x, y, 0x7]:
                # 8XY7: Sets VX to VY minus VX. VF is set to 0 when there's a borrow, and 1 when there is not.
                self.v[x] = self.v[y] - self.v[x]
                self.v[0xF] = self.v[x] < 0
                self.v[x] += 0x100 * (self.v[x] < 0)
            case [0x8, x, y, 0xE]:
                # 8XYE: Stores the most significant bit of VX in VF and then shifts VX to the left by 1.
                self.v[0xF] = self.v[x] >> 7
                self.v[x] = self.v[x] << 1 & 0xFF
            case [0x9, x, y, 0x0]:
                # 9XY0: Skips the next instruction if VX does not equal VY. (Usually the next instruction is a jump to skip a code block);
                if self.v[x] != self.v[y]:
                    self.ip += 2
            case [0xA, n2, n1, n0]:
                # ANNN: Sets I to the address NNN.
                self.i = be(n2, n1, n0)
            case [0xB, n2, n1, n0]:
                # BNNN: Jumps to the address NNN plus V0.
                self.ip = be(n2, n1, n0) + self.v[0] - 2
            case [0xC, x, n1, n0]:
                # CXNN: Sets VX to the result of a bitwise and operation on a random number (Typically: 0 to 255) and NN.
                self.v[x] = randint(0, 255) & be(n1, n0)
            case [0xD, x, y, n]:
                # DXYN: Draws a sprite at coordinate (VX, VY)
                # that has a width of 8 pixels and a height of N pixels.
                # Each row of 8 pixels is read as bit-coded starting from memory location I;
                # I value does not change after the execution of this instruction.
                # As described above, VF is set to 1 if any screen pixels are flipped from
                # set to unset when the sprite is drawn, and to 0 if that does not happen
                self.v[0xF] = 0
                for i in range(n):
                    for j in range(8):
                        self.v[0xF] |= self.set_pixel(
                            self.v[x] + j,
                            self.v[y] + i,
                            self.memory[self.i + i] >> (7 - j) & 1,
                        )
            case [0xE, x, 0x9, 0xE]:
                # EX9E: Skips the next instruction if the key stored in VX is pressed. (Usually the next instruction is a jump to skip a code block);
                if self.pressed[self.v[x]]:
                    self.ip += 2
            case [0xE, x, 0xA, 0x1]:
                # EXA1: Skips the next instruction if the key stored in VX is pressed. (Usually the next instruction is a jump to skip a code block);
                if not self.pressed[self.v[x]]:
                    self.ip += 2
            case [0xF, x, 0x0, 0x7]:
                # FX07: Sets VX to the value of the delay timer.
                self.v[x] = self.delay_timer
            case [0xF, x, 0x0, 0xA]:
                # FX0A: A key press is awaited, and then stored in VX. (Blocking Operation. All instruction halted until next key event);
                if self.last_pressed is None:
                    self.ip -= 2
                    end = True
                else:
                    self.v[x] = self.last_pressed
                    self.last_pressed = None
            case [0xF, x, 0x1, 0x5]:
                # FX15: Sets the delay timer to VX.
                self.delay_timer = self.v[x]
            case [0xF, x, 0x1, 0x8]:
                # FX18: Sets the sound timer to VX.
                self.sound_timer = self.v[x]
            case [0xF, x, 0x1, 0xE]:
                # FX1E: Adds VX to I. VF is not affected.[c]
                self.i += self.v[x]
            case [0xF, x, 0x2, 0x9]:
                # FX29: Sets I to the location of the sprite for the character in VX. Characters 0-F (in hexadecimal) are represented by a 4x5 font.
                self.i = 5 * self.v[x]
            case [0xF, x, 0x3, 0x3]:
                # FX33: Stores the binary-coded decimal representation of VX,
                # with the most significant of three digits at the address in I,
                # the middle digit at I plus 1, and the least significant digit at I plus 2.
                # (In other words, take the decimal representation of VX, place the hundreds
                # digit in memory at location in I, the tens digit at location I+1, and the ones digit at location I+2.);
                self.memory[self.i : self.i + 3] = map(
                    lambda d: int(d), f"{self.v[x]:03}"
                )
            case [0xF, x, 0x5, 0x5]:
                # FX55: Stores V0 to VX (including VX) in memory starting at address I. The offset from I is increased by 1 for each value written, but I itself is left unmodified.[d]
                self.memory[self.i : self.i + x + 1] = self.v[: x + 1]
            case [0xF, x, 0x6, 0x5]:
                # FX65: Fills V0 to VX (including VX) with values from memory starting at address I. The offset from I is increased by 1 for each value written, but I itself is left unmodified.[d]
                self.v[: x + 1] = self.memory[self.i : self.i + x + 1]
            case [n3, n2, n1, n0]:
                raise NotImplementedError(f"unknown inst: {be(n3, n2, n1, n0):04x}")
        if not all(0 <= r <= 255 for r in self.v):
            print(
                f'{inst[0] * 256 + inst[1]:04x} {self.ip:08x} {[f"{x:02x}" for x in self.v]} {self.i:08x}'
            )
            raise ValueError(f"bad reg")
        return end


c = Chip8()
with open(sys.argv[1], "rb") as f:
    c.load(f.read())
c.run()
