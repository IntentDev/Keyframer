uniform vec4 uColor;

in Vertex
{
	vec4 color;
} iVert;

// Output variable for the color
layout(location = 0) out vec4 oFragColor[TD_NUM_COLOR_BUFFERS];
void main()
{
	TDCheckDiscard();
	vec4 outcol = vec4(0.0, 0.0, 0.0, 0.0);
	outcol.rgb += uColor.rgb  * iVert.color.rgb;
	outcol.rgb *= uColor.a;
	float alpha = uColor.a * iVert.color.a ;
	outcol = TDDither(outcol);
	TDAlphaTest(alpha);
	outcol.a = alpha;
	oFragColor[0] = TDOutputSwizzle(outcol);
}
