#version 460 core

in vec4 point;

out vec2 uv;

uniform vec2 u_scale;
uniform vec2 u_offset;
uniform vec2 u_screen_size;

void main() {
  vec2 ndc = (point.xy / u_screen_size) * u_scale + u_offset;
  gl_Position = vec4(ndc, 0.0, 1.0);
  uv = point.zw;
}
