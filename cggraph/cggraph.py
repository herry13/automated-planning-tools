#!/usr/bin/env python

'''

cgGraph - generating a graphic of given causal-graph

author: Herry (herry13@gmail.com)

requirement:
- graphviz

The causal graph is in the format of: http://www.fast-downward.org/TranslatorOutputFormat
Note that mutexes and axioms are ignored.

Changelog:
31.05.2014 - first release

-----
BSD LICENSE

Copyright (c) 2014, Herry
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met: 

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer. 
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution. 

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies, 
either expressed or implied, of the FreeBSD Project.
-----

'''

import os
import sys
import subprocess

usage = '''usage: cggraph.py <sas-file> <pdf-file>
'''

class ParseException(Exception):
	pass

def process(sasfile, pdffile):
	def process_version(f):
		for i in range(0,3):
			f.readline()

	def process_metric(f):
		for i in range(0,3):
			f.readline()

	'''
	variables = [ total-values ]*  --  index represents variable's ID
	'''
	def process_variable(f):
		total = int(f.readline())
		variables = []
		for i in range(0,total):
			if f.readline().strip() != "begin_variable":
				raise ParseException("missing: begin_variable")
			name = f.readline().strip() # name
			f.readline() # axiom variable (1) or not (-1)
			nvalues = int(f.readline()) # total values
			values = [f.readline().strip() for j in range(0,nvalues)]
			variables.append(nvalues)
			if f.readline().strip() != 'end_variable':
				raise ParseException("missing: end_variable")
		return variables

	def process_mutex(f):
		total = int(f.readline())
		if total > 0:
			raise ParseException("mutex is not empty")

	'''
	state = [ value ]*  --  index represents variable's ID
	'''
	def process_state(f, nvariables):
		if f.readline().strip() != "begin_state":
			raise ParseException("missing: begin_state")
		init = [int(f.readline()) for i in range(0, nvariables)]
		if f.readline().strip() != "end_state":
			raise ParseException("missing: end_state")
		return init

	'''
	goal = [ variable, value ]*
	'''
	def process_goal(f):
		if f.readline().strip() != "begin_goal":
			raise ParseException("missing: begin_goal")
		goal = [ [int(x) for x in f.readline().split(' ')] for i in range(0,int(f.readline())) ]
		if f.readline().strip() != "end_goal":
			raise ParseException("missing: end_goal")
		return goal

	'''
	operators = [ prevails, preposts, cost ]*
	prevails  = [ variable, value ]*
	preposts  = [ variable, pre-value, post-value ]*
	cost      = int
	'''
	def process_operator(f):
		total = int(f.readline())
		operators = []
		for i in range(0,total):
			if f.readline().strip() != "begin_operator":
				raise ParseException("missing: begin_operator")
			name = f.readline().strip()
			prevails = [ [int(x) for x in f.readline().split(' ')] for j in range(0,int(f.readline())) ]
			preposts = [ [int(x) for x in f.readline().split(' ')[1:]] for j in range(0,int(f.readline())) ]
			cost = int(f.readline())
			operators.append([prevails, preposts, cost])
			if f.readline().strip() != "end_operator":
				raise ParseException("missing: end_operator")
		return operators

	'''
	edges = [from, to, weight]*
	'''
	def generate_edges(variables, operators):
		edges = {}
		for op in operators:
			for post in [prepost[0] for prepost in op[1]]:
				dest = str(post)
				# dependency edges: from is prevail-condition, to is postcondition
				for prevail in op[0]:
					key = str(prevail[0]) + "-" + dest
					edges[key] = edges[key] + 1 if key in edges else 1
				# dependency edges: from is precondition, to is postcondition
				for pre in op[1]:
					if pre[0] != post and pre[1] > 0:
						key = str(pre[0]) + "-" + dest
						edges[key] = edges[key] + 1 if key in edges else 1
				# joint-effects edges: from is postcondition (other variables), to is postcondition
				for jointpost in [prepost[0] for prepost in op[1]]:
					if jointpost != post:
						key = str(jointpost) + "-" + dest
						edges[key] = edges[key] + 1 if key in edges else 1
		return edges

	# parse SAS file
	with open(sasfile) as f:
		process_version(f)
		process_metric(f)
		variables = process_variable(f)
		process_mutex(f)
		init = process_state(f, len(variables))
		goal = process_goal(f)
		operators = process_operator(f)

	edges = generate_edges(variables, operators)
	# generate DOT file
	dot = "strict digraph {\n"
	for edge in edges.keys():
		_from, _to = edge.split('-')
		dot += "  " + _from + " -> " + _to + " [weight=" + str(edges[edge]) + "];\n"
	dot += '''}'''

	# generate graph
	dotfile = pdffile + '.dot'
	with open(dotfile, 'w') as f:
		f.write(dot)
	subprocess.call(['dot', '-Tpdf', '-o', pdffile, dotfile])
	os.remove(dotfile)

def graphviz_exist():
	p = subprocess.Popen(['which', 'dot'], stdout=subprocess.PIPE)
	out, err = p.communicate()
	return (err == None and len(str(out).strip()) > 0)

if __name__ == '__main__':
	if not graphviz_exist():
		print "Error: graphviz (dot) is not available!"
	elif len(sys.argv) != 3:
		print usage
	else:
		process(sys.argv[1], sys.argv[2])
