# import logging
# import multiprocessing
# import os
# import sys
# from datetime import datetime, timedelta
#
# import arcview
# import arcpy
#
# from ZoneofInfluence_Code.utils import multiprocessing_helpers, logger_helper
# from ZoneofInfluence_Code.utils.junction_class import JunctionData
# from ZoneofInfluence_Code.utils.multiprocessing_helpers import log_message, print_message
#
#
# def get_dbf_files(model_file, source_folder):
#     scenario_path = format_scenario_path(model_file, source_folder)
#
#     if not os.path.isdir(scenario_path):
#         return
#
#     results_list = []
#
#     for folder in os.listdir(scenario_path):
#         if is_ignore_scenarios(folder):
#             continue
#
#         results_list.extend(process_scenario_folder(scenario_path, folder))
#
#     return results_list
#
#
# def format_scenario_path(model_file, source_folder):
#     """
#     Convert the inputs of the model file and its source folder into the output scenario folders
#     """
#     logging.info("Formatting Scenario Path")
#     scenario_path_name = "{}.OUT\\SCENARIO".format(model_file.replace(".mxd", "").replace(".MXD", ""))
#     scenarioPath = os.path.join(source_folder, scenario_path_name)
#     return scenarioPath
#
#
# def is_ignore_scenarios(scenario_name):
#     """
#     Validate if the name of the scenario matches any of the ones to be ignored
#     """
#
#     if scenario_name not in ["MANNHEIM", "ERB"]:
#         return True
#     else:
#         return False
#
#     # for item in ["AVE_DAY_CURRENT","MAX_DAY_CURRENT","BASE"]:
#     #     if item in scenario_name:
#     #         return True
#     # return False
#
#
# def process_scenario_folder(scenario_path, folder):
#     full_path = os.path.join(scenario_path, folder)
#     for item in os.listdir(full_path):
#         if "JunctOut" in item:
#             return [os.path.join(folder, item)]
#     return []
#
#
# def read_model_results(model_file, source_folder, scenario_file, output_geodatabase, en):
#     logging.info("Getting Model Results data")
#     scenario, file_name = scenario_file.split("\\")
#     scenario_base = format_scenario_path(model_file, source_folder)
#     full_path = os.path.join(scenario_base, scenario_file)
#
#     table_name = create_table_name(file_name, scenario)
#
#     dbf_table = arcpy.CopyRows_management(full_path, "in_memory\\results_table_{}".format(en))
#
#     output_table, cursor_fields = create_output_table(dbf_table, output_geodatabase, table_name)
#
#     populate_output_table(cursor_fields, dbf_table, output_table)
#
#     arcpy.Delete_management(dbf_table)
#     return output_table
#
#
# def populate_output_table(cursor_fields, dbf_table, output_table):
#     logging.info("Populating output table")
#     rowcount = int(arcpy.GetCount_management(dbf_table)[0])
#     # c_obj, max_obj = create_multiprocessing_counter([1] * rowcount)
#     with arcpy.da.InsertCursor(output_table, cursor_fields) as ic:
#         with arcpy.da.SearchCursor(dbf_table, cursor_fields) as sc:
#             for line in sc:
#                 # iterate_counter(c_obj, max_obj, print_value=50000)
#                 outvalues = process_row(cursor_fields, line)
#                 ic.insertRow(outvalues)
#
#
# def process_row(cursor_fields, line):
#     base_time = datetime(int(datetime.now().year), 01, 01, 00, 00)
#     outvalues = []
#     for i in range(0, len(cursor_fields), 1):
#         var = line[i]
#         if type(var) is unicode:
#             if cursor_fields[i] == "TIME":
#                 var = var.replace("hrs", "")
#                 var = var.replace(" ", "")
#                 var = var.split(":")
#                 # takes a base time of Jan 1 and adds the hours or minutes depending on the value
#                 # in the time field
#
#                 # new code, works better then looking at the time and trying to estimate
#                 # based on the hour
#
#                 # doesn't need to be sequential, simply based on the total amount of time
#                 # within the field thats being examined
#
#                 var = base_time + timedelta(hours=int(var[0]), minutes=int(var[1]))
#                 var = var.strftime("%x %X")
#         outvalues.append(var)
#     return outvalues
#
#
# def create_output_table(dbf_table, output_geodatabase, table_name):
#     logging.info("Creating output table")
#     field_names, cursor_fields = get_field_names(dbf_table)
#
#     output_table = create_output_table_raw(output_geodatabase, table_name, field_names)
#     return output_table, cursor_fields
#
#
# def get_field_names(dbf_table):
#     cursor_fields = []
#     field_names = arcpy.ListFields(dbf_table)
#     for x in range(0, len(field_names)):
#         if field_names[x].type != "OID":
#             cursor_fields.append(field_names[x].name)
#     return field_names, cursor_fields
#
#
# def create_table_name(file, scenario):
#     """
#     Creates output name of the feature based on the feature type and the scenario
#     """
#     logging.info("Getting table name")
#     out_dct = {
#         'Junct': 'Junction',
#         'Pipe': 'Pipe',
#         'Pump': 'Pump',
#         'Res': 'Reservoir',
#         'Tank': 'Tank',
#         'Valve': 'Valve'
#     }
#
#     item_name = out_dct.get(file.replace("Out.dbf", ""))
#     if item_name is None:
#         return False
#
#     output_name = "{}_{}_{}".format(scenario, item_name, "OUT")
#     return output_name
#
#
# def create_output_table_raw(outputGDB, tableName, fields):
#     counter = 1
#     coretable = tableName
#     # while arcpy.Exists(os.path.join(outputGDB,coretable)):
#     #     coretable = "{}_{}".format(tableName,counter)
#     #     counter += 1
#     logging.info("Creating Table: {}".format(os.path.join(outputGDB,coretable)))
#     newTable = arcpy.CreateTable_management(outputGDB, coretable)[0]
#
#     for field in fields:
#         field_settings = generate_table_fields(field)
#         if field_settings != False:
#             logging.info("Adding Field: {}".format(field_settings[0]))
#             arcpy.AddField_management(newTable,field_settings[0],field_settings[1],field_settings[2],field_settings[3],field_settings[4])
#     return newTable
#
#
# def generate_table_fields(baserecord):
#     field_name = baserecord.name
#     field_type = baserecord.type
#     field_length = baserecord.length
#     field_decimals = baserecord.scale
#     field_precision = baserecord.precision
#     if field_name == "TIME":
#         return [field_name,"DATE","","",""]
#     if field_type == "OID":
#         return False
#     else:
#         return [field_name,field_type,field_precision,field_decimals,field_length]
#
#
# def create_query_table(output_geodatabase, table, feature, input_type="Junction", en=0):
#     workspace_path = set_workspace(output_geodatabase)
#     logging.info("Building Query Table parameters")
#     query_feature_params = build_query_feature_params(feature, table, input_type)
#     logging.info("Generating Query Table")
#
#     QT = arcpy.MakeQueryTable_management(query_feature_params[0],
#                                          query_feature_params[1],
#                                          "USE_KEY_FIELDS",
#                                          query_feature_params[2],
#                                          query_feature_params[3],
#                                          query_feature_params[4])
#
#     final_query_table = update_table_names(QT, table, en)
#     logging.info("Copying final Query Table to {}".format(query_feature_params[5]))
#     result = arcpy.CopyFeatures_management(
#         final_query_table,
#         os.path.join(workspace_path,query_feature_params[5]))[0]
#     return result
#
#
# def set_workspace(geodatabase):
#     arcpy.env.workspace = geodatabase
#     return geodatabase
#
#
# def build_query_feature_params(feature, table, input_type):
#     feature_name = feature.split("\\")[-1]
#     table_name = table.split("\\")[-1]
#
#     outputfeature = create_output_query_table_name(table_name)
#
#     tableList = [feature,table]
#
#     keyfield = "{}.ID".format(feature_name)
#
#     sql = "{}.ID = {}.ID".format(feature_name, table_name)
#
#     feature_field = get_feature_fields(feature_name, input_type)
#
#     tableField = get_table_fields(table, table_name)
#
#     combinedFields = []
#     for item in (feature_field + tableField):
#         combinedFields.append([item])
#
#     return [tableList, "QueryTable", keyfield, combinedFields, sql, outputfeature]
#
#
# def get_table_fields(table, table_name):
#     tableField = []
#     for item in arcpy.ListFields(table):
#         if item.name not in ["TIME_STEP", "OBJECTID"]:
#             tableField.append("{}.{}".format(table_name, item.name))
#     return tableField
#
#
# def get_feature_fields(feature_name, input_type):
#     list_item = get_feature_field_list(input_type)
#     feature_field = []
#     for item in list_item:
#         feature_field.append("{}.{}".format(feature_name, item))
#     return feature_field
#
#
# def get_feature_field_list(inputType):
#     if (inputType == "Junction"):
#         ls = ["ID", "ELEVATION", "ZONE", "FILTER_TYP", "Shape"]
#     elif inputType == "Pipe":
#         ls = ["ID", "ZONE", "FROM_", "TO", "Shape"]
#     else:
#         ls = ["ID", "ZONE", "Shape"]
#     return ls
#
#
# def create_output_query_table_name(table):
#     outfile = ''
#     baseList = ["Junction","Pipe","Pump","Reservoir","Valve","Tank"]
#     for i in baseList:
#         if i.upper() in table.upper():
#             outfile = table.replace("OUT","QT")
#             break
#     return outfile
#
#
# def update_table_names(query_table, table_path, en):
#     field_list, field_list_str, raw_fields_str = get_field_lists(query_table, table_path)
#
#     sr = arcpy.SpatialReference(26917)
#
#     tmpFeature = arcpy.CreateFeatureclass_management("in_memory", "tmp_feature_{}".format(en), "POINT", spatial_reference=sr)
#     for field in field_list:
#         arcpy.AddField_management(tmpFeature,field.name,field.type,field.precision,field.scale,field.length)
#
#     field_list_str.append("SHAPE@XY")
#     raw_fields_str.append("SHAPE@XY")
#
#     logging.info("Updating Table Field Names")
#     with arcpy.da.InsertCursor(tmpFeature,field_list_str) as ic:
#         with arcpy.da.SearchCursor(query_table, raw_fields_str) as sc:
#             for row in sc:
#                 ic.insertRow(row)
#
#     return tmpFeature
#
#
# def get_field_lists(query_table, table_path):
#     replace_fields = ["{}_".format(table_path.split("\\")[-1]), "Junction_"]
#
#     raw_fieldsstr = []
#     field_liststr = []
#     field_list = []
#     for fields in arcpy.ListFields(query_table):
#         if fields.type in ["OID", "Geometry"]:
#             continue
#
#         raw_fieldsstr.append(fields.name)
#
#         fieldName = fields.name
#         for item in replace_fields:
#             fieldName = fieldName.replace(item, "")
#
#         # checks for duplicate field names and appends a number on the end
#         c = 1
#         while True:
#             if fieldName not in field_liststr:
#                 break
#             fieldName = "{}_{}".format(fieldName, c)
#             c += 1
#
#         fields.name = fieldName
#         field_list.append(fields)
#         field_liststr.append(fieldName)
#     return field_list, field_liststr, raw_fieldsstr
#
#
# def generate_averaged_feature(table, junctions_feature, output_geodatabase, en):
#     logging.info("Generating Average Table")
#     base_scenario = table.split("\\")[-1]
#     scenario = "{}_AVERAGE".format(base_scenario.split("_")[0])
#
#     fields = get_average_fields(table)
#
#     summation_dictionary = create_sum_table(fields, table, en)
#
#     junction_dictionary = build_junction_class_dictionary(junctions_feature, summation_dictionary)
#
#     temp_table = create_averaged_table(fields, junction_dictionary, scenario, table, en)
#
#     return arcpy.CopyFeatures_management(temp_table, os.path.join(output_geodatabase, scenario))[0]
#
#
# def create_averaged_table(fields, junction_dictionary, scenario, table, en):
#     logging.info("Creating Average Feature")
#     temp_table = arcpy.CreateFeatureclass_management("in_memory", "{}_{}".format(scenario, en), "POINT", table,
#                                                      spatial_reference=arcpy.SpatialReference(26917))
#     logging.info("Loading Average Feature Data")
#     with arcpy.da.InsertCursor(temp_table, fields) as ic:
#         for item in junction_dictionary:
#             junction = None
#             junction = junction_dictionary[item]
#
#             newRow = (junction.junctionID,
#                       junction.junctionElevation,
#                       junction.junctionZone,
#                       junction.junctionFilterType,
#                       junction.junctionOutID,
#                       junction.getAverageDemand(),
#                       junction.getAverageHead(),
#                       junction.getAveragePressure(),
#                       junction.getAverageAge(),
#                       junction.junctionShape)
#
#             ic.insertRow(newRow)
#     return temp_table
#
#
# def build_junction_class_dictionary(junctions_feature, summation_dictionary):
#     logging.info("Building Junction Class Objects")
#     junction_dictionary = {}
#     with arcpy.da.SearchCursor(junctions_feature, ["ID", "ELEVATION", "ZONE", "FILTER_TYP", "SHAPE@XY"]) as sc:
#         for row in sc:
#             junction = None
#             junction = junction_dictionary.get(row[0])
#             if junction is None:
#                 junction = JunctionData(row[0], row[1], row[2], row[3], row[0], row[4])
#                 junction_dictionary[row[0]] = junction
#
#             dmd, hd, press, qual = summation_dictionary[row[0]]
#             junction.AddDemandValue(dmd)
#             junction.AddHeadValue(hd)
#             junction.AddPressureValue(press)
#             junction.AddAgeValue(qual)
#     return junction_dictionary
#
#
# def create_sum_table(fields, table, en):
#     logging.info("Creating Summation Results")
#     summation_table = calculate_table_statistics(fields, table, en)
#     summation_dictionary = {}
#     with arcpy.da.SearchCursor(summation_table,
#                                ["ID", "MEAN_DEMAND", "MEAN_HEAD", "MEAN_PRESSURE", "MEAN_QUALITY"]) as sc:
#         for row in sc:
#             summation_dictionary[row[0]] = [row[1], row[2], row[3], row[4]]
#     return summation_dictionary
#
#
# def calculate_table_statistics(fields, table, en):
#     logging.info("Calculating Statistics on {}".format(table))
#     summation_table = arcpy.Statistics_analysis(table, "in_memory\\sumtbl_{}".format(en),
#                                                 [[fields[5], "MEAN"],
#                                                  [fields[6], "MEAN"],
#                                                  [fields[7], "MEAN"],
#                                                  [fields[8], "MEAN"]],
#                                                 ["ID"])
#     return summation_table
#
#
# def get_average_fields(table):
#     logging.info("Getting fields")
#     outFields = []
#     for field in arcpy.ListFields(table):
#         if field.type in ["OID","Geometry"]: continue
#         if "TIME" in field.name.upper(): continue
#         outFields.append(field.name)
#     outFields.append("SHAPE@XY")
#     return outFields
#
#
# def process_model_results(scenarios, model_file, model_folder, junction_shapefiles, output_model_data, basedir, cpu_count):
#     manager = multiprocessing.Manager()
#     l = manager.Lock()
#     queue_list = multiprocessing_helpers.create_queue_from_list([item for item in scenarios], manager)
#     queue_full = []
#
#     output_tables = []
#     def cb(res):
#         output_tables.extend(res)
#
#     # generate_data((queue_list, config.model_file, config.model_folder, config.junction_shapefiles,
#     #           config.output_model_data, l, 0))
#
#     pool = multiprocessing.Pool(processes=cpu_count)
#     # for item in range(0, multiprocessing.cpu_count()):
#     for item in range(0, cpu_count):
#         pool.apply_async(
#             generate_data,
#             ((queue_list, model_file, model_folder, junction_shapefiles,
#               output_model_data, l, item, basedir),),
#             callback=cb
#         )
#     pool.close()
#     pool.join()
#
# def generate_data(values):
#     try:
#         arcpy.env.overwriteOutput = True
#         arcpy.SetLogHistory(False)
#         queue_item, model_path, model_folder, junction_features, output_folder, lock_item, en, basedir = values
#         results = []
#
#         logger_helper.setup_logger(basedir, save_file=True, stream=False)
#         try:
#             while True:
#                 item = queue_item.get_nowait()
#                 scenario = item.split("\\")[0]
#                 print_message(lock_item, "Starting {}".format(scenario))
#                 output_geodatabase = create_output_geodatabase(output_folder, scenario)
#                 junction_features = load_junctions_into_geodatabase(output_geodatabase, junction_features)
#
#                 print_message(lock_item, "loading model results {}".format(scenario))
#                 gdb_dbf_feature = read_model_results(model_path, model_folder, item, output_geodatabase, en)
#
#                 print_message(lock_item, "Creating query tables {}".format(scenario))
#                 feature_qt = create_query_table(output_geodatabase, gdb_dbf_feature, junction_features, en=en)
#
#                 print_message(lock_item, "Generating Average Junctions {}".format(scenario))
#                 results.append(
#                     [
#                         generate_averaged_feature(feature_qt, junction_features, output_geodatabase, en),
#                         output_geodatabase
#                     ]
#                 )
#         except:
#             return results
#
#     except Exception as e:
#         logging.info(e.message)
#         logging.info(sys.exc_traceback.tb_lineno)
#
#
# def create_output_geodatabase(folder_path, geodatabase_name):
#     geodatabase_path = os.path.join(folder_path, "{}.gdb".format(geodatabase_name))
#     if not arcpy.Exists(geodatabase_path):
#         arcpy.CreateFileGDB_management(folder_path, geodatabase_name)
#     return geodatabase_path
#
#
# def load_junctions_into_geodatabase(geodatabase, junctions):
#     return arcpy.CopyFeatures_management(junctions, os.path.join(geodatabase, "junctions"))[0]
