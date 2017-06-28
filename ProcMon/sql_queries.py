from re import match
from sqlite3 import connect
from time import sleep


def initialize_db(filename):
	global db
	global conn

	if not filename:
		print("[!] Initialization could not find a suitable file")
		print("[!] Please standby while we initialize the database")
		sleep(1)
		filename = input("[?] Enter your db name: ")
		filetype = '.*\.proc'
		if not match(filetype, filename):
			filename = filename + '.proc'
	conn = connect(filename)
	db = conn.cursor()
	create_table("process_map", "(proc_name TEXT, file_hash TEXT, uniq_proc_table_name TEXT)")
	conn.commit()


def does_item_exist(tablename, col_name, entry):
	db.execute("SELECT * FROM '{tn}' WHERE {cn}='{entry}'".format(tn=tablename, cn=col_name, entry=entry))
	exists = db.fetchall()
	#print("Exists: ", exists)
	if exists is not None:
		return True
	else:
		return False


def recall_entry(recall, tablename, col, row_value):
	"""Select col_name1 FROM tablename WHERE col_name2=row_value"""
	db.execute("SELECT {cn} FROM '{tn}' WHERE {col}='{rv}'".format(cn=recall, tn=tablename, col=col, rv=row_value))
	data = db.fetchall()
	return data


def add_new_entry(tablename, col_values_tup):
	"""
	PROCESSES TABLE:
		# 0 - process id (primary key)
		# 1 - pid name
		# 2 - path to the process's file
		# 3 - hash of the file in #3
		# 4 - the status of the process
		# 5 - the process working dir
		# 6 - process's running permissions
		# 7 - any file the process has open
		# 8 - l_tuple - (listening addr,lport)
		# 9 - r_tuple - (remote addr,rport)
		# 10 - the state of the connection
		# 11 - children processes tuple in tuple with children details ((child1 name1, child1 exe-path1),(2,2).....)
	"""

	# The below loop formats the VALUES literal into the form of (?,?,?)
	# and dynamically expands based on the # of values
	literals = "("
	for elem in col_values_tup:
		literals = literals + "?"
		if col_values_tup[-1] == elem:
			literals = literals + ",?)"  # add an extra element to account for the primary key
		# to be added later int his function
		else:
			literals = literals + ","
		# literal = str(tuple(get_columns(tablename))[1:])
		# print(literal)

		# The first column in any table is the primary key
		# command = "INSERT INTO {tn} {cns} VALUES {literals}, {col_values}".format(tn=tablename,cns=tuple(get_columns(tablename)),
		# literals=literals,col_values=col_values)
	col_names = get_columns(tablename)
#	print("[*] Columns for table", tablename, " ", col_names)
	sql = "INSERT INTO '{tn}' {cns} VALUES {col_values}".format(tn=tablename, cns=col_names,
	                                                            col_values=format_cols_for_dbvalues(col_values_tup))
#	print("[*] SQL String: ", sql)
	db.execute("INSERT INTO '{tn}' {cns} VALUES {col_values}".format(tn=tablename, cns=col_names,
	                                                                 col_values=format_cols_for_dbvalues(
		                                                                 col_values_tup)))
	conn.commit()


def format_cols_for_dbvalues(value_li):
	# puts into this format: ('4','first','last','33'), made for values to be inserted
	i = 0
	values = "("
	while i < len(value_li):
		if i < len(value_li) - 1:
			values = '{v}"{vl}",'.format(v=values, vl=value_li[i])

		else:
			values = '{v}"{vl}")'.format(v=values, vl=value_li[i])

		i = i + 1
	return values


def get_columns(tablename):
	"With a tablename, the function returns the columns as a list"
	sql = "pragma table_info('{tn}')".format(tn=tablename)
#	print("[*] SQL: ", sql)
	table_returns = db.execute("pragma table_info('{tn}')".format(tn=tablename))
	rlist = ()
	for r in table_returns:
		rlist = rlist + (r[1],)
	return rlist


def does_table_exist(tablename):
	db.execute("SELECT * FROM sqlite_master WHERE name='{tn}' and type='table' ".format(tn=tablename))
	client_table_exists = db.fetchone()
	if client_table_exists:
		return True
	else:
		return False


def create_table(tablename, table_cols):
	table_exists = does_table_exist(tablename)
	if not table_exists:
		db.execute("CREATE TABLE '{tn}' {cns}".format(tn=tablename, cns=table_cols))
		conn.commit()
	# input(print("[i] Created ", tablename, " Table - Press enter to continue..."))
	else:
		#        print("[!] Table already exists")
		pass
