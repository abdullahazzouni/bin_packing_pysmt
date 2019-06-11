# bin_packing_pysmt
An implementation of the bin-packing problem using PySMT

This work was submitted as a class project for Oregon State University's CS 517 Spring 
2019 class.

The idea is to model servicing of datacenter requests as a bin-packing problem, a known 
NP-hard problem. Then, reducing this problem to a Satisfiable format, an implementation
was built using PySMT (https://github.com/pysmt/pysmt).

The input is a csv file of the following format:
line 1: dummy_text, width, length
line 2 onwards: request_id, width, length
