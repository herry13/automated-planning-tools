#!/usr/bin/env python

'''

cgGraph - generating a graphic of given causal-graph

author: Herry (herry13@gmail.com)

requirement:
- networkx (python)
- pygraphviz (python)
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
import networkx as nx

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
		names = []
		for i in range(0,total):
			if f.readline().strip() != "begin_variable":
				raise ParseException("missing: begin_variable")
			names.append(f.readline().strip()) # name
			f.readline() # axiom variable (1) or not (-1)
			nvalues = int(f.readline()) # total values
			values = [f.readline().strip() for j in range(0,nvalues)]
			variables.append(nvalues)
			if f.readline().strip() != 'end_variable':
				raise ParseException("missing: end_variable")
		yield variables
		yield names

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

	def graph_to_pdf(G, outfile, remove_dot=True):
		nx.write_dot(G, outfile + ".dot")
		subprocess.call(['dot', '-Tpdf', '-o', outfile, outfile + ".dot"])
		if remove_dot:
			os.remove(outfile + ".dot")


	# create an empty graph
	G = nx.DiGraph()

	# parse SAS file
	with open(sasfile) as f:
		process_version(f)
		process_metric(f)
		variables, names = process_variable(f)
		process_mutex(f)
		init = process_state(f, len(variables))
		goal = process_goal(f)
		operators = process_operator(f)

	# compute directed edges (causal-links) between variables
	edges = generate_edges(variables, operators)

	# add nodes to graph
	for i in range(0,len(variables)):
		G.add_node(i, {'size': variables[i], 'label': names[i]})
	# add edges to graph
	for edge in edges.keys():
		_from, _to = edge.split('-')
		G.add_edge(_from, _to, {'weight': edges[edge]})

	# generate graph file
	graph_to_pdf(G, pdffile)

	'''# remove nodes without edges
	G1 = nx.DiGraph()
	indegrees = G.in_degree()
	outdegrees = G.out_degree()
	for node in G.nodes():
		if indegrees[node] > 0 or outdegrees[node] > 0:
			G1.add_node(node)
	G1.add_edges_from(G.edges())
	graph_to_pdf(G1, 'withedges.pdf', False)

	# remove acyclic edges
	G2 = nx.DiGraph()
	G2.add_nodes_from(G1.nodes())
	G2.add_edges_from(G1.edges())
	for node in G2.nodes():
		for successor in G2.successors(node):
			if not G2.has_edge(successor, node):
				G2.remove_edge(node, successor)
	indegrees = G2.in_degree()
	outdegrees = G2.out_degree()
	for node in indegrees.keys():
		if indegrees[node] <= 0:
			G2.remove_node(node)
		else:
			print(str(node) + " " + names[int(node)] + " - " \
			      + str(indegrees[node]) + "," + str(outdegrees[node]) \
			      + "," + str(variables[int(node)]))
	graph_to_pdf(G2, 'cyclic.pdf', False)
	
	#G2 = G
	indegrees = G2.in_degree()
	w = max(indegrees.values())
	# remove edges whose weight is the maximum
	G3 = nx.DiGraph()
	G3.add_nodes_from(G2.nodes())
	G3.add_edges_from(G2.edges())
	for node in indegrees.keys():
		if indegrees[node] == w:
			G3.remove_node(node)
	graph_to_pdf(G3, 'no_max_indegrees.pdf')'''


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
