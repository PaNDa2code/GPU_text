#version 460 core

in vec2 point;

uniform vec2 u_scale;
uniform vec2 u_offset;
uniform vec2 u_screen_size;

void main() {
  vec2 ndc = (point / u_screen_size) * u_scale + u_offset;
  gl_Position = vec4(ndc, 0.0, 1.0);
}
