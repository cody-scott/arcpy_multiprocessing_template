import multiprocessing
from utils.multiprocessing_helpers \
    import create_queue_from_list, print_message

import arcview
import arcpy

def multi_work(list_of_things=[], cpu_count=1):
    manager = multiprocessing.Manager()
    lock_var = manager.Lock()
    queue_list = create_queue_from_list([item for item in list_of_things], manager)
    queue_full = []

    output_tables = []
    def callback_func(res):
        output_tables.extend(res)

    pool = multiprocessing.Pool(processes=cpu_count)
    for item in range(0, cpu_count):
        pool.apply_async(
            generate_data,
            ((queue_list, lock_var),),
            callback=callback_func
        )
    pool.close()
    pool.join()


def generate_data(values):
    arcpy.env.overwriteOutput = True
    arcpy.SetLogHistory(False)

    queue_item, lock_item = values
    results = []

    try:
        while True:
            item = queue_item.get_nowait()
            scenario = item.split("\\")[0]
            print_message(lock_item, "Starting {}".format(scenario))

    except:
        return results