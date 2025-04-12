#version 330

// Input from vertex shader
in vec2 fragTexCoord;

// Output color
out vec4 fragColor;

// Uniforms
uniform vec3 color;            // Base color (RGB)
uniform float bloom_intensity; // Intensity of bloom/glow effect

void main() {
    // Calculate distance from center for radial gradient
    // Use squared distance to avoid expensive sqrt operation
    vec2 center = vec2(0.5, 0.5);
    vec2 delta = fragTexCoord - center;
    float dist_squared = dot(delta, delta);
    float dist = sqrt(dist_squared); // Only calculate sqrt once
    
    // Create circular shape with soft edges - use faster approximation
    // Precompute edge values
    const float inner_edge = 0.45;
    const float outer_edge = 0.55;
    float circle = 1.0 - clamp((dist - inner_edge) / (outer_edge - inner_edge), 0.0, 1.0);
    
    // Apply bloom effect (glow that extends beyond the circle)
    // Use linear interpolation instead of smoothstep for better performance
    float bloom_edge = 0.75 + 0.3 * bloom_intensity;
    float bloom = 1.0 - clamp((dist - inner_edge) / (bloom_edge - inner_edge), 0.0, 1.0);
    
    // Use multiplication instead of pow for better performance
    bloom = bloom * bloom * bloom_intensity;
    
    // Calculate final intensity
    float intensity = circle + bloom * 0.7;
    
    // Apply color with glow
    vec3 glowColor = color * intensity;
    
    // Enhance brightness for neon effect - use faster approximation
    // sqrt is faster than pow for this case
    glowColor = sqrt(glowColor * 0.64); // Approximates pow(x, 0.8)
    
    // Output final color with alpha
    fragColor = vec4(glowColor, intensity);
}
