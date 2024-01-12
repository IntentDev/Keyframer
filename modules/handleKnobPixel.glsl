uniform vec4 uColor;
uniform vec4 uSelColor;
uniform sampler2D sLocked;
uniform sampler2D sUnlocked;

vec4 cols[2];


in Vertex
{
	vec4 color;
	vec4 customAttrib0;	
	mat4 worldTransform;
	flat bool locked;	
} iVert;

// Output variable for the color
layout(location = 0) out vec4 oFragColor[TD_NUM_COLOR_BUFFERS];
void main()
{
	// This allows things such as order independent transparency
	// and Dual-Paraboloid rendering to work properly
	TDCheckDiscard();
	int viewState = int(ceil(iVert.customAttrib0.y));	
	cols[0] = uColor;
	cols[1] = uSelColor;
	vec4 col = cols[viewState];
	
	vec4 coord = vec4(gl_PointCoord.st, 0.0, 0.0);
	coord.xy = 2.0 * coord.xy - 1.0;
	coord.xyz = mat3(iVert.worldTransform) * coord.xyz;
	coord.xy = .5 * coord.xy + .5;
	
	vec4 outcol = vec4(0.0);
	if (iVert.locked == true)
	{
		outcol = texture(sLocked, coord.xy);
	}
	else
	{
		outcol = texture(sUnlocked, coord.xy);
	}


	outcol.rgb *= col.rgb * iVert.color.rgb;

	// Alpha Calculation
	float alpha = outcol.a * uColor.a * iVert.color.a;

	// Dithering, does nothing if dithering is disabled
	outcol = TDDither(outcol);

	outcol.rgb *= alpha;

	// Modern GL removed the implicit alpha test, so we need to apply
	// it manually here. This function does nothing if alpha test is disabled.
	TDAlphaTest(alpha);
	outcol.a = alpha;
	oFragColor[0] = TDOutputSwizzle(outcol);

	// TD_NUM_COLOR_BUFFERS will be set to the number of color buffers
	// active in the render. By default we want to output zero to every
	// buffer except the first one.
	for (int i = 1; i < TD_NUM_COLOR_BUFFERS; i++)
	{
		oFragColor[i] = vec4(0.0);
	}
}
