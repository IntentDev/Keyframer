uniform ivec2 uAnimRange;
uniform float uPointYChop[512];
// use for chop array with more than 512 samples (large view...)
// uniform samplerBuffer uPointYChop;

out Vertex
{
	vec4 color;
} oVert;

void main()
{
	vec4 adjPos = vec4(P, 1.0);
	adjPos.y += uPointYChop[gl_VertexID];
	// use for chop array with more than 512 samples (large view...)
	// adjPos.y += texelFetch(uPointYChop, index).x;
	vec4 worldCamPos = uTDMats[0].worldCam * adjPos;
	worldCamPos.x = P.x;
	vec4 projPos = uTDMats[0].proj * worldCamPos;
	// projPos.z += 1;
	projPos = TDPickAdjust(projPos, 0);	
	gl_Position = projPos;

#ifndef TD_PICKING_ACTIVE
	vec4 worldCamInvPos = uTDMats[0].worldCamInverse * adjPos;
	if (worldCamInvPos.x < uAnimRange.x || worldCamInvPos.x > uAnimRange.y)
	{
		oVert.color = mix(vec4(.5), vec4(.0), int(P.x * 2) % 2);
	}
	else
	{
		oVert.color = TDInstanceColor(Cd);
	}

	TDWritePickingValues();
#else // TD_PICKING_ACTIVE
	TDWritePickingValues();
	// vTDPickVert.camSpacePosition = worldCamPos.xyz;
	// vTDPickVert.worldSpacePosition = adjPos.xyz;
#endif // TD_PICKING_ACTIVE
}
