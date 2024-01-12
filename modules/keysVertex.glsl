uniform float uPointSize;

out Vertex
{
	vec4 color;
	vec4 customAttrib0;
} oVert;

void main()
{

	// First deform the vertex and normal
	// TDDeform always returns values in world space
	gl_PointSize = uPointSize;
	vec3 pos = P;
	//pos.xy *= scaleSize;
	vec4 worldSpacePos = TDDeform(pos);
	gl_Position = TDWorldToProj(worldSpacePos);

	oVert.customAttrib0 = TDInstanceCustomAttrib0();

	// This is here to ensure we only execute lighting etc. code
	// when we need it. If picking is active we don't need lighting, so
	// this entire block of code will be ommited from the compile.
	// The TD_PICKING_ACTIVE define will be set automatically when
	// picking is active.
#ifndef TD_PICKING_ACTIVE
	oVert.color = TDInstanceColor(Cd);

#else // TD_PICKING_ACTIVE
	// This will automatically write out the nessessary values
	// for this shader to work with picking.
	// See the documentation if you want to write custom values for picking.
	TDWritePickingValues();
	vTDCustomPickVert.indices = ivec4(TDInstanceCustomAttrib1());

#endif // TD_PICKING_ACTIVE
}
