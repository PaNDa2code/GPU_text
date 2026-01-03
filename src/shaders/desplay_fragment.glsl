#version 330 core

out vec4 color;
uniform sampler2D u_tex;

void main() {
  ivec2 p = ivec2(gl_FragCoord.xy);
  int i = int(texelFetch(u_tex, p, 0).r * 255.0) & 1;
  color = vec4(i, i, i, 1.0);
}
