import multiprocessing
import logging

import arcview
import arcpy
import os
import shutil
import sys

def temp_folder_required(func):
    def func_wrapper(*args):
        create_temp_folder()
        return func(*args)
    return func_wrapper


def iterate_counter(count_i, max_count, print_always=False, change_value=1, print_value=50):
    """
    Iterates the locking counter
    :param count_i:
    :type count_i:
    :param thread:
    :type thread:
    :param max_count:
    :type max_count:
    :param print_always:
    :type print_always:
    :return:
    :rtype:
    """
    print_flag = False
    with count_i.get_lock():
        count_i.value += change_value
        if (count_i.value % print_value) == 0:
            print_flag = True
        elif count_i.value >= max_count:
            print_flag = True

        if print_flag is True or print_always is True:
            print("{} of {}".format(count_i.value, max_count))
        return


def join_results(results):
    logging.info("Joining Results")
    return_list = []
    for item in results:
        return_list.extend(item)
    return return_list


def create_multiprocessing_counter(list_value, manager=None):
    logging.info("Creating Multiprocessing Counter")
    if manager is None:
        manager = multiprocessing.Manager()

    count_item_multi = manager.Value('i', 0)
    max_count_multi = len(list_value)

    return count_item_multi, max_count_multi


def create_queue_from_list(list_values, manager=None):
    """
    Build a simple queue object from the supplied junction list
    :param list_values:
    :type list_values:
    :return:
    :rtype:
    """
    logging.info("Constructing queue object")
    if manager is None:
        manager = multiprocessing.Manager()

    new_queue = manager.Queue()
    for item in list_values:
        new_queue.put(item)

    logging.info("Queue constructed")
    return new_queue


@temp_folder_required
def create_temporary_shapefiles(feature, feature_name):
    """
    Create the temporary shapefiles in the temporary folder
    :param feature:
    :type feature:
    :param feature_name:
    :type feature_name:
    :return:
    :rtype:
    """
    logging.info("Creating temporary shapefile in temp folder: {}".format(feature_name))
    return arcpy.FeatureClassToFeatureClass_conversion(feature,
                                                       os.path.join(os.environ['appdata'], "TMP"),
                                                       feature_name)[0]


def get_item_from_queue(queue_item, spatial_reference):
    """
    Gets the next item from the queue and converts it to proper format
    :param queue_item:
    :type queue_item:
    :return:
    :rtype:
    """
    queue_value = queue_item.get()
    feature_id, geometry_wkt = queue_value
    geometry = arcpy.FromWKT(geometry_wkt, spatial_reference)
    return feature_id, geometry


def feature_id_shape_to_list(feature, sql="", id_field="ID"):
    logging.info("Converting {} to list of ID and WKT Geometries".format(feature))
    out_list = []
    with arcpy.da.SearchCursor(feature, [id_field, "SHAPE@"], sql) as sc:
        for row in sc:
            out_list.append([row[0], row[1].WKT])
    return out_list


def feature_id_shape_to_dict(feature, sql="", id_field="OID@"):
    feature_list = feature_id_shape_to_list(feature, sql, id_field)
    out_dictionary = {
        item[0]: item[1]
        for item in feature_list
        }
    return out_dictionary


def create_temp_folder():
    tmp_folder = os.path.join(os.environ['appdata'], "TMP")
    if not os.path.isdir(tmp_folder):
        logging.info("Creating temporary folder {}".format(tmp_folder))
        os.mkdir(tmp_folder)
    return


def load_layer_to_memory(feature, feature_name):
    logging.info("Loading into memory: {}".format(feature_name))
    return arcpy.CopyFeatures_management(feature, "in_memory\\{}".format(feature_name))


def create_feature_layer(feature, feature_layer_name):
    logging.info("Creating feature layer: {}_FL".format(feature_layer_name))
    return arcpy.MakeFeatureLayer_management(feature, "{}_FL".format(feature_layer_name))


def delete_temporary_folder_and_files():
    try:
        tmp_folder = os.path.join(os.environ['appdata'], "TMP")
        shutil.rmtree(tmp_folder)
    except:
        logging.error("Problem removing temporary folder")


def log_message(lock_item, message):
    lock_item.acquire()
    logging.info(message)
    lock_item.release()


def print_message(lock_item, message):
    lock_item.acquire()
    print(message)
    lock_item.release()
    log_message(lock_item, message)


def set_multi_exec():
    multiprocessing.set_executable(
        os.path.join(get_install_path(), 'pythonw.exe'))


def get_install_path():
    ''' Return 64bit python install path from registry (if installed and registered),
        otherwise fall back to current 32bit process install path.
    '''
    if sys.maxsize > 2**32: return sys.exec_prefix #We're running in a 64bit process

    #We're 32 bit so see if there's a 64bit install
    path = r'SOFTWARE\Python\PythonCore\2.7'

    from _winreg import OpenKey, QueryValue
    from _winreg import HKEY_LOCAL_MACHINE, KEY_READ, KEY_WOW64_64KEY

    try:
        with OpenKey(HKEY_LOCAL_MACHINE, path, 0, KEY_READ | KEY_WOW64_64KEY) as key:
            return QueryValue(key, "InstallPath").strip(os.sep) #We have a 64bit install, so return that.
    except: return sys.exec_prefix #No 64bit, so return 32bit path