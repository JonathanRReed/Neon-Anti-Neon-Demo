#version 330

// Input from vertex shader
in vec2 fragTexCoord;

// Output color
out vec4 fragColor;

// Uniforms
uniform vec3 core_color;       // Core color (RGB)
uniform vec3 halo_color;       // Halo color (RGB)
uniform float halo_width;      // Width of the halo ring (0.02 - 0.4)
uniform float halo_intensity;  // Intensity multiplier for halo (0.0 - 2.0)
uniform float bloom_intensity; // Additional bloom/glow effect strength

void main() {
    // Calculate distance from center
    vec2 center = vec2(0.5, 0.5);
    vec2 delta = fragTexCoord - center;
    float dist = length(delta);

    // Core region parameters
    const float core_radius = 0.46;       // base circle radius
    float core_edge = 0.02;               // edge softness for core

    // Core mask (smooth edge)
    float core = 1.0 - smoothstep(core_radius, core_radius + core_edge, dist);

    // Halo mask: ring around the core
    float halo_outer = core_radius + halo_width;
    float halo = smoothstep(core_radius, core_radius + 0.5 * halo_width, dist)
               * (1.0 - smoothstep(core_radius + 0.5 * halo_width, halo_outer, dist));

    // Base color composition
    vec3 color = core_color * core + halo_color * halo * halo_intensity;

    // Bloom: extend glow beyond halo using multiple falloffs
    float bloom1 = 1.0 - smoothstep(core_radius, core_radius + halo_width * 1.6, dist);
    float bloom2 = 1.0 - smoothstep(core_radius + halo_width * 0.8, core_radius + halo_width * 2.2, dist);
    float bloom = (bloom1 * 0.7 + bloom2 * 0.3) * bloom_intensity;

    // Apply bloom to halo color only (preserve dark core if desired)
    color += halo_color * bloom * halo_intensity * 0.6;

    // Subtle chromatic aberration on far glow for richness
    if (dist > core_radius + halo_width * 0.6) {
        float t = clamp((dist - (core_radius + halo_width * 0.6)) / (0.6 - halo_width * 0.6), 0.0, 1.0);
        color.r *= 1.0 + t * 0.25;
        color.b *= 1.0 - t * 0.15;
    }

    // Gentle non-linear brightness for "neon" feel
    color = sqrt(color * 0.8);

    // Final alpha: stronger where either core or halo present
    float alpha = clamp(core + halo + bloom * 0.5, 0.0, 1.0);

    fragColor = vec4(clamp(color, 0.0, 1.0), alpha);
}
