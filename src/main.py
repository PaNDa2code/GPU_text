import moderngl
import moderngl_window as mglw
import numpy as np
import os
import freetype as ft
import random
import string

from font import *


def read_file(path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, path)
    with open(full_path, "r") as f:
        return f.read()


vertex_shader = read_file("shaders/vertex.glsl")
fragment_shader = read_file("shaders/fragment.glsl")

desplay_vertex_shader = read_file("shaders/desplay_vertex.glsl")
desplay_fragment_shader = read_file("shaders/desplay_fragment.glsl")


class App(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "GPU Text Rendering"
    window_size = (800, 600)
    aspect_ratio = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.prog = self.ctx.program(vertex_shader, fragment_shader)
        self.display_prog = self.ctx.program(
            desplay_vertex_shader, desplay_fragment_shader
        )

        self.create_frame_buffer()

        self.points_vbo = self.ctx.buffer(reserve=10000, dynamic=True)

        self.vao = self.ctx.vertex_array(
            self.prog,
            [
                (self.points_vbo, "4f", "point"),
            ],
        )

        self.display_vao = self.ctx.vertex_array(self.display_prog, [])

        self.face = ft.Face("fonts/FreeSans.ttf")
        self.face.set_char_size(64, 64)

        self.face.load_char("A", ft.FT_LOAD_NO_HINTING)

        self.scale = [1.0, 1.0]
        self.offset = [0.0, 0.0]
        self.last_glyph_time = 0
        self.random_glyph = True

    def on_unicode_char_entered(self, char: str) -> None:
        if char == " ":
            self.random_glyph = not self.random_glyph
        else:
            self.face.load_char(char, ft.FT_LOAD_NO_HINTING)

    def update_uniforms(self) -> None:
        self.prog["u_scale"] = self.scale
        self.prog["u_offset"] = self.offset
        self.prog["u_screen_size"] = self.window_size

    def create_frame_buffer(self) -> None:
        self.tex = self.ctx.texture(self.window_size, 1)
        self.tex.filter = moderngl.NEAREST, moderngl.NEAREST
        self.tex.repeat_x = False
        self.tex.repeat_y = False

        self.fbo = self.ctx.framebuffer([self.tex])

    def on_resize(self, width: int, height: int) -> None:
        self.window_size = width, height

        self.tex.release()
        self.fbo.release()
        self.create_frame_buffer()

        self.pass1_tex = self.ctx.texture((width, height), 1)
        self.pass1_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)

        self.update_uniforms()

    def on_mouse_scroll_event(self, x_offset: float, y_offset: float) -> None:
        self.scale[0] = max(0.5, self.scale[0] + y_offset)
        self.scale[1] = max(0.5, self.scale[1] + y_offset)
        self.update_uniforms()

    def on_mouse_drag_event(self, x: int, y: int, dx: int, dy: int) -> None:
        self.offset[0] += dx / self.window_size[0] * 2
        self.offset[1] -= dy / self.window_size[1] * 2
        self.update_uniforms()

    def on_key_event(self, key, action, modifiers) -> None:
        if key == self.wnd.keys.SPACE:
            self.random_glyph = not self.random_glyph

    def on_render(self, time, frame_time):
        if self.random_glyph and time - self.last_glyph_time >= 1.0:
            self.last_glyph_time = time

            char = random.choice(string.ascii_letters)
            self.face.load_char(char, ft.FT_LOAD_NO_HINTING)

        self.fbo.use()
        self.fbo.clear(0.0, 0.0, 0.0, 1)

        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.ONE, moderngl.ONE

        outline = self.face.glyph.outline
        geometry = generate_glyph_geometry(outline)

        self.points_vbo.write(geometry.tobytes())
        self.vao.render(moderngl.TRIANGLES, vertices=len(geometry))

        self.ctx.disable(moderngl.BLEND)

        self.ctx.screen.use()
        self.ctx.screen.clear(0.0, 0.0, 0.0, 1)

        self.tex.use(0)
        self.display_prog["u_tex"] = 0

        self.display_vao.render(moderngl.TRIANGLES, vertices=3)


def main():
    mglw.run_window_config(App)


if __name__ == "__main__":
    main()
