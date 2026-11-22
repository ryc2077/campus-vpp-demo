shader_type canvas_item;

// Godot 4.4：SCREEN_TEXTURE 内建量已移除，须显式声明为带 hint_screen_texture 的 uniform。
uniform sampler2D SCREEN_TEXTURE : hint_screen_texture, filter_linear_mipmap;
// 液态玻璃（Liquid Glass）——浮层控件专用。
// 取值来源 martin65536/liquid-glass-webgl（Kyant AndroidLiquidGlass 的 WebGL 移植）：
//  - 可分离高斯模糊：separable-blur.ts，Skia convertRadiusToSigma σ = radius*0.57735+0.5，
//    预乘 alpha 保护（只对 alpha>0 样本加权）；本 shader 用单遍 9-tap 十字高斯近似
//    （两遍分离需要中间 FBO，Godot canvas_item 单 shader 做不到；十字核在小半径下误差可接受）。
//  - G2 连续曲率：sdf.ts 注明解析圆角矩形 SDF 与贝塞尔 G2 曲线的偏差 <0.5% 半径
//    （亚像素级），故直接用解析 sdRoundBox，不预计算 SDF 纹理。
//  - 色差：element.ts 的 7 通道色散只在透镜边缘生效；这里只在 rim 带内做 R/B 双通道偏移。
//  - 饱和度：源码 ColorFilter 用 1.5；UI 上文字可读优先，只取 1.15。
//  - 内阴影：源码是 Canvas2D 后处理；这里用 rim 带内的反向渐变近似。
// 用法：挂在 ColorRect（GlassSurface）上，作为内容节点的 *sibling*（不做父容器），
// 避免 shader 被继承到文字/按钮上。文字面板（ScenePanel/ABCPanel）保持实色，
// 保证深色文字在稳定底色上 ≥4.5:1；玻璃只用在直接浮在 3D 场景上的两处：
// 场景栏（底部）和天气切换胶囊（右上）。同屏玻璃元素 2 个，远低于 10 个上限。
// 降级：?glass=0 或 SCREEN_TEXTURE 不可用时，由 GlassSurface 隐藏自己并显示实色 fallback。

uniform vec2 rect_size = vec2(660.0, 56.0);
uniform float corner_radius = 28.0; // 胶囊角 = 高/2
uniform float blur_radius = 6.0;    // px（低质量 4.0）
uniform int tap_mode = 1;           // 0 = 5 taps（窄屏/低端），1 = 9 taps（默认）
uniform vec3 tint_color : source_color = vec3(1.0);
uniform float tint_alpha = 0.42;    // 白色提亮：深色文字在模糊背景上仍可读
uniform float refraction_px = 2.5;  // 边缘折射：往中心方向小偏移
uniform float chromatic_px = 1.2;   // 边缘色差：R/B 沿法线反向偏移
uniform float rim_light = 0.28;     // 细亮边（左上光）
uniform float inner_shadow = 0.10;  // 内阴影（右下）
uniform float saturation = 1.15;

float sd_round_box(vec2 p, vec2 b, float r) {
	vec2 q = abs(p) - b + r;
	return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}

void fragment() {
	vec2 px = UV * rect_size;
	vec2 c = px - rect_size * 0.5;
	vec2 half = rect_size * 0.5 - corner_radius;
	float sd = sd_round_box(c, half, corner_radius);
	// 边缘 1px smoothstep 抗锯齿；alpha≈0 的角外区域后续计算仍会跑完，
	// 但 COLOR 的 alpha 为 0，视觉上就是透明（Godot shader 不允许 fragment 里 return）
	float alpha = 1.0 - smoothstep(0.0, 1.0, sd);
	// SDF 梯度 ≈ 外法线（中心差分，边缘处 |grad|≈1）
	float e = 1.0;
	vec2 grad = vec2(
		sd_round_box(c + vec2(e, 0.0), half, corner_radius) - sd_round_box(c - vec2(e, 0.0), half, corner_radius),
		sd_round_box(c + vec2(0.0, e), half, corner_radius) - sd_round_box(c - vec2(0.0, e), half, corner_radius)
	) * 0.5;
	// rim 带：边缘 1，往内 10px 衰到 0；折射与色差只在这里生效
	float rim = 1.0 - clamp(-sd / 10.0, 0.0, 1.0);
	vec2 suv = FRAGCOORD.xy * SCREEN_PIXEL_SIZE;
	vec2 refr = -grad * rim * refraction_px * SCREEN_PIXEL_SIZE;
	vec2 base_uv = suv + refr;
	// 9-tap 十字高斯：中心 0.32，±r/2 各 0.13（4 个），±r 各 0.04（4 个），和为 1
	float r = blur_radius;
	vec2 pxs = SCREEN_PIXEL_SIZE;
	vec3 col;
	if (tap_mode > 0) {
		col = texture(SCREEN_TEXTURE, base_uv).rgb * 0.32;
		col += texture(SCREEN_TEXTURE, base_uv + vec2(r * 0.5, 0.0) * pxs).rgb * 0.13;
		col += texture(SCREEN_TEXTURE, base_uv - vec2(r * 0.5, 0.0) * pxs).rgb * 0.13;
		col += texture(SCREEN_TEXTURE, base_uv + vec2(0.0, r * 0.5) * pxs).rgb * 0.13;
		col += texture(SCREEN_TEXTURE, base_uv - vec2(0.0, r * 0.5) * pxs).rgb * 0.13;
		col += texture(SCREEN_TEXTURE, base_uv + vec2(r, 0.0) * pxs).rgb * 0.04;
		col += texture(SCREEN_TEXTURE, base_uv - vec2(r, 0.0) * pxs).rgb * 0.04;
		col += texture(SCREEN_TEXTURE, base_uv + vec2(0.0, r) * pxs).rgb * 0.04;
		col += texture(SCREEN_TEXTURE, base_uv - vec2(0.0, r) * pxs).rgb * 0.04;
	} else {
		// 5-tap 低质量：中心 0.4，十字 ±r 各 0.15
		col = texture(SCREEN_TEXTURE, base_uv).rgb * 0.40;
		col += texture(SCREEN_TEXTURE, base_uv + vec2(r, 0.0) * pxs).rgb * 0.15;
		col += texture(SCREEN_TEXTURE, base_uv - vec2(r, 0.0) * pxs).rgb * 0.15;
		col += texture(SCREEN_TEXTURE, base_uv + vec2(0.0, r) * pxs).rgb * 0.15;
		col += texture(SCREEN_TEXTURE, base_uv - vec2(0.0, r) * pxs).rgb * 0.15;
	}
	// 边缘色差：R/B 沿法线反向各偏 chromatic_px（只在 rim 带内）
	if (rim > 0.01) {
		vec2 cd = grad * rim * chromatic_px * pxs;
		col.r = texture(SCREEN_TEXTURE, base_uv + cd).r;
		col.b = texture(SCREEN_TEXTURE, base_uv - cd).b;
	}
	// 克制版饱和度提升
	float luma = dot(col, vec3(0.299, 0.587, 0.114));
	col = mix(vec3(luma), col, saturation);
	// 白色提亮（保证其上深色文字对比度）
	col = mix(col, tint_color, tint_alpha);
	// 细亮边（左上）+ 内阴影（右下）：UV 系 y 向下，左上法线 ≈ (-0.55, -0.83)
	vec2 light_dir = normalize(vec2(-0.55, -0.83));
	float hi = rim * max(0.0, dot(grad, light_dir)) * rim_light;
	float sh = rim * max(0.0, dot(grad, -light_dir)) * inner_shadow;
	col = col * (1.0 - sh) + vec3(1.0) * hi;
	COLOR = vec4(col, alpha);
}
