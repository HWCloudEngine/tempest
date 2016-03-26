__author__ = 'Administrator'
import tempest.api.hybrid_cloud.compute.servers.test_servers_operations as test_servers_operations
import traceback

if __name__ == '__main__':
    test_module_dir = 'tempest.api.hybrid_cloud.compute.servers.test_servers_operations'
    hybrid_test_classes = [item for item in dir(test_servers_operations) if item.startswith('Hybrid')]
    print('hybrid test class: %s' % hybrid_test_classes)
    my_classes = {}
    for test_class in hybrid_test_classes:
        try:
            tmp_class = getattr(test_servers_operations, test_class)
            dir_class = dir(tmp_class)
            test_cases_list = [case for case in dir_class if case.startswith('test_')]
            my_classes[test_class] = test_cases_list
        except Exception, e:
            print('error: %s' % traceback.format_exc(e))
            continue

    print('all cases: %s' % str(my_classes))
