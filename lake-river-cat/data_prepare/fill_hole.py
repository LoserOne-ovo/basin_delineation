from osgeo import ogr



def fill_hole(in_shp, out_shp):

    inDs = ogr.Open(in_shp)
    inLayer = inDs.GetLayer()
    inSRS = inLayer.GetSpatialRef()

    flag = False
    # 检查是否都是Polygon
    for feature in inLayer:
        geom = feature.GetGeometryRef()
        if geom.GetGeometryType() != 3:
            flag = True
            break
    if flag:
        inDs.Destroy()
        print("GeomeType of lake must be polygon!")
        exit(-1)

    shpDrv = ogr.GetDriverByName("ESRI Shapefile")
    outDs = shpDrv.CreateDataSource(out_shp)
    outLayer = outDs.CreateLayer("data", srs=inSRS, geom_type=ogr.wkbPolygon)
    inLayerDefn = inLayer.GetLayerDefn()
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)

    for inFeature in inLayer:
        # Create output Feature
        outFeature = inFeature.Clone()
        geom = inFeature.GetGeometryRef()
        if geom.GetGeometryCount() > 1:
            sub_geom = ogr.ForceToPolygon(geom.GetGeometryRef(0))
        else:
            sub_geom = geom

        outFeature.SetGeometry(sub_geom)
        outLayer.CreateFeature(outFeature)
        outFeature = None

    outLayer.SyncToDisk()
    outDs.Destroy()
    inDs.Destroy()


if __name__ == "__main__":

    arg1 = r"D:\demo\Lakes\Asia\Asia_Lakes_lt2.shp"
    arg2 = r"D:\demo\Asia\lake\Asia_lakes.shp"
    fill_hole(arg1, arg2)

