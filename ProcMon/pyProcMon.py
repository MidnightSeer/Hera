from datetime import datetime
from os import listdir
from re import match as matched
from time import sleep
from uuid import uuid4
import argparse,SendToFile
from sys import exit,argv

import hashlib
import psutil

import sql_queries as query


class ProcessEnum:
	def __init__(self, process):
		try:
			self.process = process
			self.pid = self.process[6]
			# Add a try block in case the process disappears
			self.proc_obj = psutil.Process(self.pid)
			self.name = self.proc_obj.name()
			self.exe_path = self.proc_obj.exe()
			self.file_hash = hash_file(self.exe_path)
			self.status = self.proc_obj.status()
			self.cwd = self.proc_obj.cwd()
			self.userperm = self.proc_obj.username()
			self.open_files = self.proc_obj.open_files()
			self.id = uuid4().hex
			self.recorded_time = datetime.now().isoformat()
			# define the process children
			children_list = []
			children = self.proc_obj.children()
			if children:
				for child in children:
					children_list.append((child.pid, child.name(), child.exe(), hash_file(child.exe())))
			# store all info in a tuple

			# The following are the mappings
			# Below are the mappings for the Parent Tuple
			#  - recorded timestamp
			#  - process id --> not to be confused with a Primary Key
			#  - pid name
			#  - path to the process's file
			#  - hash of the file in #3
			#  - the status of the process
			#  - the process working dir
			#  - process's running permissions
			#  - any file the process has open
			#  - l_tuple - (listening addr,lport)
			#  - r_tuple - (remote addr,rport)
			#  - the state of the connection
			#  - children processes tuple in tuple with children details ((child1 name1, child1 exe-path1),(2,2).....)
			# The Following is the mapping for any children tuples
			# 0 - child pid
			# 1 - chile process name
			# 2 - path to child process exe
			# 3 - hash of #2
				# Load the tuple with as much pertinent info about the process
				# and associated netowkr connections
			self.proc_tup = (
				self.recorded_time, self.pid, self.proc_obj.name(), self.proc_obj.exe(),
				hash_file(self.proc_obj.exe()), self.proc_obj.status(), self.proc_obj.cwd(), self.proc_obj.username(),
				self.proc_obj.open_files(),
				self.process[3], self.process[4], self.process[5], children_list)


		except psutil.NoSuchProcess:
			print("[!] Process Disappeared! --> {proc}".format(proc=self.process))
			pass

	def logic_control(self):
		"This function stores the process into the main process map"
		# By default, the process should NOT be whitelisted
		whitelist = False
		duplicate = False
		uniq = True
		# Step 1 - Check if the process name already exists
		exists = query.does_item_exist("process_map", "proc_name", self.file_hash)

		# If process name exists, does it have the same executable hash
		if exists:

			old_hash = query.recall_entry("file_hash", "process_map", "proc_name", self.name)
			# print(old_hash)
			current_hash = self.file_hash
			i = 0
			duplicate = False
			for hash in old_hash:
				# print("Comparing: ",hash[0],current_hash)
				if hash[0] == current_hash:
					duplicate = True
				else:
					uniq = True
					pass
				i = + 1

		if duplicate:
			# If is does, pass //whitelist = False
			whitelist = False  # item is already whitelisted, we do not need to add a new entry

		elif uniq:
			print("[!] Discovered a possible rogue process")
			# Step 2 - Ask the user if you want to whitelist the new process
			ans = input("[?] Do you wish to whitelist this process ({pn})? [y/n] ".format(pn=self.name))
			# If yes
			if ans.upper() == "Y":
				whitelist = True
			else:
				whitelist = False
				whitelist = IOC_Found("new", self.name)

		else:
			#This is when the process does not match the whitelisted info
			# Do not log/whitelist the process //whitelist = False
			# But give the user an opportunity to over ride it

			whitelist = False

			# print to the screen that an IOC was found!
			# potential over ride the control to NOT whitelist
			whitelist = IOC_Found("mismatch", self.name)

		# Step 3 -- If we are whitelisting, add the entry to the main process_map table
		if whitelist:
			self.whitelistProcess()


	def whitelistProcess(self):
		# Add the entry to the process map table --> store_proc_entry
		data = (self.name, self.file_hash, self.id)
		self.store_proc_entry(data)

		# Create a table with the uniq hex id
		query.create_table(self.id,
		                   """(recorded_time TEXT, pid INTEGER, pid_name TEXT, pid_file_path TEXT, pid_file_hash TEXT, pid_status TEXT,
		                   pid_cwd TEXT, pid_run_as_user TEXT, pid_open_files TEXT, pid_listen TEXT,
		                   pid_remote_conn TEXT, pid_conn_state TEXT, pid_children TEXT)""")

		# Add the process tuple data --> store_proc_info
		self.store_proc_info(self.proc_tup)

	def store_proc_entry(self, data):
		# This function stores the data tuple into the process_map table
		query.add_new_entry("process_map", data)

	def store_proc_info(self, data):
		# This function stores the data tuple into the process specific table
		# Step 1 - find the process specific tablename
		tablename = query.recall_entry("uniq_proc_table_name", "process_map", "proc_name", self.name)

		# Step 2 - add the process tuple (data) as a new entry into the table

		query.add_new_entry(tablename[0][0], data)


def hash_file(file):
	hashed = hashlib.sha256()
	with open(file, 'rb') as ofile:
		buf = ofile.read()
		hashed.update(buf)
	return hashed.hexdigest()


def check_file(hashed_file, new_file):
	password, salt = hashed_file.split(':')
	hashed = hashlib.sha256(salt.encode() + new_file.encode()).hexdigest()
	return password == hashed


def IOC_Found(criteria, name):

	if criteria == "mismatch":
		print("[*] Process {n} is a mismatch with previously recorded process info".format(n=name))
		ans = input("[?] Do you wish to whitelist this process anyways ({pn})? [y/n] ".format(pn=name))


	elif criteria == "new":
		ans = input("[?] Do you wish to whitelist this process anyways ({pn})? [y/n] ".format(pn=name))

	if ans.upper() == "Y":
		whitelist = True
	else:
		whitelist = False
	return whitelist


def baseline_procs():
	# not currently used
	conn_list = psutil.net_connections()  # Return a tuple
	net_list = []  # maps a pid to its process information
	family_names = []
	# the proc_tup tuple contains objects related to the current process
	# a series of proc_tup tuples are in the larger net_tup tuple

	for process in conn_list:
		ProcessEnum(process)


def scan_for_file():
	match_found = False
	files = listdir(path='./')
	pattern = '.*\.proc$'
	matches_list = []
	for item in files:
		match = matched(pattern, item)
		if match:
			#            print(match.group(0))
			matches_list.append(str(match.group(0)))
			match_found = True
	if len(matches_list) > 1:
		print("[!] Found multiple possible database files")
		print(*matches_list, sep=',')
		filename = input("[?] Choose your file: ")
		#        print(filename)
		return filename
	if match_found and len(matches_list) == 1:
		#        print(matches_list[0])
		return matches_list[0]
	else:
		return ''


def scan_processes(interval):
	try:
		while True:
			conn_list = psutil.net_connections()
			for process in conn_list:
				proc = ProcessEnum(process)
				proc.logic_control()
			# print_to_file(baseline_procs())
			print("[*] Sleeping for {i} minute".format(i=interval))
			sleep(interval * 60)
	except KeyboardInterrupt:
		print("[*] Keyboard Interrupt Detected!")


def assign_args():
	global flags

	if not len(argv[1:]):
		print("[*] Did not detect any options")
		print("[*] Try [script] -h or --help to view the help menu")
		exit(0)
	else:

		parser = argparse.ArgumentParser(description="Process Baseline Tool", formatter_class=argparse.RawDescriptionHelpFormatter,
		        epilog='''Examples:
                ''')

		parser.add_argument('-f', '--file', action='store', dest='filename'
		                    , help='file to export the process data to', metavar="[File Name]")
		parser.add_argument('-l', '--live', action='store_true', dest='live'
		                    , help='perform a live process baseline analysis')
		args = parser.parse_args()
		return args
if __name__ == '__main__':
	args = assign_args()

#	if args.filename:
#		SendToFile.print_to_file()

	filename = scan_for_file()
	query.initialize_db(filename)
	interval = input("Define scan interval [minutes]: ")
	scan_processes(int(interval))  # interval (in minutes) to scan for running processes
