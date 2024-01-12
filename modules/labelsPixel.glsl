uniform vec4 uColor;
in Vertex
{
	vec4 color;
	flat uint instanceTextureIndex;
	vec2 texCoord0;
} iVert;

// Output variable for the color
layout(location = 0) out vec4 oFragColor[TD_NUM_COLOR_BUFFERS];
void main()
{
	TDCheckDiscard();
	vec4 outcol = vec4(0.0, 0.0, 0.0, 0.0);
	vec2 texCoord0 = iVert.texCoord0.st;
	vec4 emitMapColor = TDInstanceTexture(iVert.instanceTextureIndex, texCoord0.st);
	outcol.rgb += uColor.rgb * emitMapColor.rgb * iVert.color.rgb;
	outcol.rgb *= uColor.a;
	float alpha = uColor.a * emitMapColor.a * iVert.color.a ;
	outcol = TDDither(outcol);
	TDAlphaTest(alpha);
	outcol.a = alpha;
	oFragColor[0] = TDOutputSwizzle(outcol);
}
