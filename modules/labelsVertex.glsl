
out Vertex
{
	vec4 color;
	flat uint instanceTextureIndex;
	vec2 texCoord0;
} oVert;

void main()
{

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[0]);
		oVert.texCoord0.st = texcoord.st;
	}
	vec4 p = vec4(P, 1.0);
	gl_Position = uTDMats[0].proj * uTDMats[0].world * TDInstanceMat() * p;

#ifndef TD_PICKING_ACTIVE
	oVert.color = TDInstanceColor(Cd);
	oVert.instanceTextureIndex = uint(TDInstanceTextureIndex());

#else // TD_PICKING_ACTIVE

	// This will automatically write out the nessessary values
	// for this shader to work with picking.
	// See the documentation if you want to write custom values for picking.
	TDWritePickingValues();

#endif // TD_PICKING_ACTIVE
}
