#version 330

// Input from vertex shader
in vec2 fragTexCoord;

// Output color
out vec4 fragColor;

// Uniforms
uniform vec3 color;             // Base color (RGB)
uniform float shadow_intensity; // Intensity of shadow effect

void main() {
    // Calculate distance from center for radial gradient
    // Use squared distance to avoid expensive sqrt operation
    vec2 center = vec2(0.5, 0.5);
    vec2 delta = fragTexCoord - center;
    float dist_squared = dot(delta, delta);
    float dist = sqrt(dist_squared); // Only calculate sqrt once
    
    // Create circular shape with soft edges - use faster approximation
    // Precompute edge values
    const float inner_edge = 0.43;
    const float outer_edge = 0.57;
    float circle = 1.0 - clamp((dist - inner_edge) / (outer_edge - inner_edge), 0.0, 1.0);
    
    // Enhanced shadow effect with multiple layers
    // Use linear interpolation instead of smoothstep for better performance
    const float shadow_inner = 0.35;
    const float shadow_outer = 0.65;
    float shadow = clamp((dist - shadow_inner) / (shadow_outer - shadow_inner), 0.0, 1.0) * shadow_intensity;
    
    // Add secondary shadow for more depth
    const float shadow2_inner = 0.55;
    const float shadow2_outer = 0.75;
    float shadow2 = clamp((dist - shadow2_inner) / (shadow2_outer - shadow2_inner), 0.0, 1.0) * shadow_intensity * 0.5;
    
    // Combine shadow effects
    float total_shadow = shadow + shadow2;
    
    // Calculate final intensity
    float intensity = circle - total_shadow * 0.4;
    
    // Enhanced desaturation for anti-neon effect - use dot product for luminance
    float luminance = dot(color, vec3(0.299, 0.587, 0.114));
    vec3 desaturated = color * 0.7 + vec3(luminance) * 0.3;
    
    // Reduce brightness with subtle variation
    desaturated *= 0.7;
    
    // Add subtle ambient highlighting to maintain visual interest
    // Replace expensive pow with simpler calculations
    float highlight = (1.0 - dist * 1.5);
    highlight = highlight * highlight * highlight; // cube instead of pow
    highlight = clamp(highlight, 0.0, 1.0);
    
    // Add subtle rim lighting for more depth
    float rim = 1.0 - abs(dist - 0.8) * 5.0;
    rim = clamp(rim, 0.0, 1.0);
    rim *= rim; // Square for tighter falloff
    
    vec3 finalColor = mix(desaturated, desaturated * 1.1, highlight);
    finalColor += vec3(rim * 0.1) * (1.0 - shadow_intensity); // Subtle rim light
    
    // Add very subtle noise for texture
    vec2 noise_coord = fragTexCoord * 30.0;
    float noise = fract(sin(dot(noise_coord, vec2(12.9898, 78.233))) * 43758.5453);
    noise = (noise - 0.5) * 0.01; // Very subtle noise
    finalColor += vec3(noise) * 0.3;
    
    // Clamp final color
    finalColor = clamp(finalColor, 0.0, 1.0);
    
    // Output final color with alpha
    fragColor = vec4(finalColor * intensity, intensity);
}
