#version 330

// Input vertex attributes
in vec2 in_position;
in vec2 in_texcoord;

// Output to fragment shader
out vec2 fragTexCoord;

void main() {
    // Pass texture coordinates to fragment shader
    fragTexCoord = in_texcoord;
    
    // Output position
    gl_Position = vec4(in_position, 0.0, 1.0);
}
