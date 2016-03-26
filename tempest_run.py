#!/usr/bin/env python
#coding=utf-8
#date:2016.4
#author:liulongzhu

import HTMLTestRunner
import unittest,time
import re,os,sys

def createsuite(test_dir):
    testunit=unittest.TestSuite()

    discover=unittest.defaultTestLoader.discover(test_dir,pattern='test_*.py',top_level_dir=None)
    for test_case in discover:
        print test_case
        testunit.addTests(test_case)
    print testunit
    return testunit 

if __name__ == '__main__':

    tempest_module=sys.argv[1]
    print tempest_module

    if tempest_module=='jacket':
        print "run tempest for jacket"
	test_dir='tempest/api/hybrid_cloud/'
#        test_dir='tempest/api/hybrid_cloud/compute/flavors/'
        report_name='tempestReport_jacket'
    elif tempest_module=='conveyor':
        print "run tempest for conveyor"
        test_dir='tempest/api/conveyor/'
        report_name='tempestReport_conveyor'
    
    filename = '/var/lib/jenkins/jobs/CI-Test/workspace/'+report_name+'.html'
    fp = file(filename,'wb')
    runner = HTMLTestRunner.HTMLTestRunner(stream=fp,title=u'Tempest Report',description=u'用例执行情况:')

    alltestnames = createsuite(test_dir)
    runner.run(alltestnames)
    fp.close()
