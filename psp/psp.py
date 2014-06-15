#!/usr/bin/env python

'''

PSP: Python SAS Planner
Author: Herry (herry13@gmail.com)

Requirements:
- Python 2.x

'''

import sys

class Operator(object):
	def __init__(self, name):
		self.name = name
		self.cost = 0
		self.pre = {}
		self.post = {}

	def __str__(self):
		return self.name #+ " " + str(self.pre) + " " + str(self.post)

	def __repr__(self):
		return self.__str__()

	def __clone__(self):
		operator = Operator(self.name)
		operator.cost = self.cost
		for k, v in self.pre.iteritems():
			operator.pre[k] = v
		for k, v in self.post.iteritems():
			operator.post[k] = v
		return operator

	def to_deterministic(self, variable_sizes):
		operators = [self]
		for k, v in self.post.iteritems():
			if k not in self.pre and variable_sizes[k] > 1:
				temp = []
				for i in range(0,variable_sizes[k]):
					if i != v:
						for op in operators:
							opx = op.__clone__()
							opx.pre[k] = i
							temp.append(opx)
				operators = temp
		return operators

	def support(self, goal):
		supporter = False
		contradict = False
		for k, v in self.post.iteritems():
			if k in goal:
				if goal[k] == v:
					supporter = True
				else:
					contradict = True
		for k, v in self.pre.iteritems():
			if k not in self.post and k in goal:
				if goal[k] != v:
					supporter = False
		return (supporter and not contradict)

	def apply_backward(self, goal, copy=False):
		for k, v in self.pre.iteritems():
			goal[k] = v
		return goal

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
			goal = {}
			for i in range(0,int(f.readline())):
				var, val = f.readline().split(' ')
				goal[int(var)] = int(val)
			if f.readline().strip() != "end_goal":
				raise ParseException("missing: end_goal")
			return goal
	
		def process_operators(f, variable_sizes):
			total = int(f.readline())
			non_deterministic_backward = False
			operators = []
			for i in range(0,total):
				ndb = False
				if f.readline().strip() != "begin_operator":
					raise ParseException("missing: begin_operator")
				operator = Operator(f.readline().strip())
				# prevail conditions
				for j in range(0,int(f.readline())):
					prevail = f.readline().split(' ')
					operator.pre[int(prevail[0])] = int(prevail[1])
				# pre-post conditions
				for j in range(0,int(f.readline())):
					prepost = f.readline().split(' ')
					var = int(prepost[1])
					pre = int(prepost[2])
					if pre > -1:
						operator.pre[var] = pre
					else:
						non_deterministic_backward = ndb = True
					operator.post[var] = int(prepost[3])
				# cost
				operator.cost = int(f.readline())
				if f.readline().strip() != "end_operator":
					raise ParseException("missing: end_operator")
				if ndb:
					operators += operator.to_deterministic(variable_sizes)
				else:
					operators.append(operator)
			yield operators
			#yield non_deterministic_backward
			yield False

		with open(sas_file) as f:
			process_version(f)
			process_metric(f)
			self.variable_sizes, self.variable_names = process_variable(f)
			process_mutex(f)
			self.state = process_state(f, len(self.variable_names))
			self.goal = process_goal(f)
			self.operators, self.non_deterministic_backward = process_operators(f, self.variable_sizes)

		'''print self.state
		for op in self.operators:
			print op, op.applicable_backward(self.state)
		print "non deterministic backward: ", self.non_deterministic_backward'''

	def at_goal(self):
		for k, v in self.goal.iteritems():
			if self.state[k] !=  v:
				return False
		return True

	def get_flaws(self):
		flaws = {}
		for k, v in self.goal.iteritems():
			if self.state[k] != v:
				flaws[k] = v
		return flaws

	def get_supporters(self):
		supporters = []
		flaws = self.get_flaws()
		#print "flaws:", flaws
		for operator in self.operators:
			if operator.support(flaws):
				supporters.append(operator)
		supporters.sort()
		return supporters

	def plan(self):
		plan = []
		print self.goal
		print self.get_supporters()
		while not self.at_goal():
			operators = self.get_supporters()
			if len(operators) <= 0: # dead-end
				print "dead-end:" #, plan
				break
			else:
				#print operators
				self.goal = operators[0].apply_backward(self.goal)
				#print "apply: ", operators[0]
				'''print self.goal
				print self.get_supporters()
				break'''
				plan.append(operators[0])

		plan = [op for op in reversed(plan)]
		#print "plan:", plan
		for op in plan:
			print op

usage = '''Usage: psp.py <sas-file>
'''

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print(usage)
	else:
		psp = PSP(sys.argv[1])
		psp.plan()
