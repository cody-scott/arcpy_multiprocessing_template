example has full example of the code implemented
multi_worker has outline

If passing arcpy classes convert to well known text geometries to pass in and handle appropriately.
Will need to convert these from Geometries to WKT and back before sending.

Can only send native python classes, hence no arcpy geometry.

Can't share between processes.

Need to consider what you're doing and structure the rest of your code appropriately.
Example would be writing to geodatabases. Can't do it multiprocess, so need to create multiple, then have those return, then write something to merge them all back into one.
Could write to shapefiles instead.

Can't write rasters to the same folder. Need to write each one to its own subfolder.


"code" is the single tool template

Toolbox is the python toolbox example.

Code should be transferable between the single use and the toolbox