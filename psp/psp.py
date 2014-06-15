#!/usr/bin/env python

'''

PSP: Python SAS Planner
Author: Herry (herry13@gmail.com)

Requirements:
- Python 2.x

'''

import sys

class Operator(object):
	'''
	@param name operator's name
	'''
	def __init__(self, name):
		self.name = name
		self.cost = 0
		self.pre = {}
		self.post = {}

	'''def __clone__(self):
		op = Operator(self.name)
		op.cost = self.cost
		for k, v in self.pre.iteritems():
			op[k] = v
		for k, v in self.post.iteritems():
			op[k] = v
		return op'''

	def __str__(self):
		return self.name + " " + str(self.pre)

	def __repr(self):
		return self.__str__()

	def support(self, goals):
		for g in goals:
			if g[0] in self.post.keys() and self.post[g[0]] == g[1]:
				return True
		return False

	def apply_backward(self, state, goal, variable_sizes):
		pass # TODO

'''
	def applicable_forward(self, state):
		for k, v in self.pre.iteritems():
			if state[k] != v:
				return False
		return True

	def apply_forward(self, state):
		for k, v in self.post.iteritems():
			state[k] = v
		return state

	def applicable_backward(self, state):
		for k, v in self.post.iteritems():
			if state[k] != v:
				return False
		return True'''

class PSP(object):
	def __init__(self, sas_file):
		self.parse_file(sas_file)

	def at_goal(self):
		for g in self.goal:
			if self.state[g[0]] != g[1]:
				return False
		return True

	def parse_file(self, sas_file):
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
				f.readline() # unsupported -- axiom variable (1) or not (-1) (TODO)
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
	
		def process_operators(f):
			total = int(f.readline())
			non_deterministic_backward = False
			operators = []
			for i in range(0,total):
				if f.readline().strip() != "begin_operator":
					raise ParseException("missing: begin_operator")
				operator = Operator(f.readline().strip())
				for j in range(0,int(f.readline())):
					prevail = f.readline().split(' ')
					operator.pre[int(prevail[0])] = int(prevail[1])
				for j in range(0,int(f.readline())):
					prepost = f.readline().split(' ')
					var = int(prepost[1])
					pre = int(prepost[2])
					if pre > -1:
						operator.pre[var] = pre
					else:
						non_deterministic_backward = True
					operator.post[var] = int(prepost[3])
				operator.cost = int(f.readline())
				operators.append(operator)
				if f.readline().strip() != "end_operator":
					raise ParseException("missing: end_operator")
			yield operators
			yield non_deterministic_backward

		with open(sas_file) as f:
			process_version(f)
			process_metric(f)
			self.variable_sizes, self.variable_names = process_variable(f)
			process_mutex(f)
			self.state = process_state(f, len(self.variable_names))
			self.goal = process_goal(f)
			self.operators, self.non_deterministic_backward = process_operators(f)

		'''print self.state
		for op in self.operators:
			print op, op.applicable_backward(self.state)
		print "non deterministic backward: ", self.non_deterministic_backward'''

	def get_flaws(self):
		flaws = []
		for g in self.goal:
			if self.state[g[0]] != g[1]:
				flaws.append(g)
		return flaws

	def get_supporters(self):
		supporters = []
		flaws = self.get_flaws()
		for operator in self.operators:
			if operator.support(flaws):
				supporters.append(operator)
		supporters.sort()
		return supporters

	def plan(self):
		plan = []
		while not self.at_goal():
			operators = self.get_supporters()
			if len(operators) <= 0: # dead-end
				print "dead-end!"
				break
			else:
				break

		print "plan:", plan

usage = '''Usage: psp.py <sas-file>
'''

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print(usage)
	else:
		psp = PSP(sys.argv[1])
		psp.plan()
