
uniform vec2 uPointSize;
uniform vec3 uRenderSize;

out Vertex
{
	vec4 color;
	vec4 customAttrib0;	
	mat4 worldTransform;
	flat bool locked;
} oVert;

void main()
{

	// First deform the vertex and normal
	// TDDeform always returns values in world space
	vec3 pos = P;
	vec4 wPos0 = TDDeform(P);
	vec4 pPos0 = TDWorldToProj(wPos0);

	pos.x += TDInstanceCustomAttrib0().x; 
	vec4 wPos1 = TDDeform(pos);
	vec4 pPos1 = TDWorldToProj(wPos1);
	
	gl_Position = pPos1;
	vec4 customAttrib0 = TDInstanceCustomAttrib0();
	oVert.customAttrib0 = customAttrib0;
	oVert.locked = bool(customAttrib0.z);
	oVert.worldTransform = TDInstanceMat();

	vec3 delta = pPos1.xyz - pPos0.xyz;
	float len = length(delta * uRenderSize);
	float sizeMix = len / uPointSize.x;

	gl_PointSize = mix(uPointSize.x, uPointSize.y, clamp(sizeMix, 0., 1.));

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
	// vTDPickVert.color = vec4(int(customAttrib0.w), 0, 0, 0);
	vTDCustomPickVert.indices = ivec4(TDInstanceCustomAttrib1());

#endif // TD_PICKING_ACTIVE
}
