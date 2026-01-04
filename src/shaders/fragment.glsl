#version 460 core

in vec2 uv;
out vec4 frag_color;

void main() {
  if (uv.x * uv.x > uv.y)
    discard;

  frag_color = vec4(1.0 / 255.0, 0.0, 0.0, 1.0);
}
