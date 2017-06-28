#This file initializes the database
import sqlite3, os, re
from time import sleep
import sql_queries as dbq

def init_table_col_names(table_type):
    if table_type == 'client':
        clients_table_cols = """
                    (table_id INTEGER, state TEXT, local_address TEXT, local_port INTEGER, remote_address TEXT, remote_port INTEGER, process_name TEXT,
                    process_file_loc TEXT, proc_file_hash TEXT, status TEXT, username TEXT, cpu_usage FLOAT, )
                        """
        return clients_table_cols

def db_setup():
    setup = False
    init_log_file = False

    if not dbq.check_table('client'):
        print("[!] Setup is establishing space for client records...")
        dbq.create_table('client',init_table_col_names('client'))
        sleep(1)
        setup = True

def scan_for_file():
    match_found = False
    files = os.listdir(path='./')
    pattern = '.*\.cr$'
    matches_list = []
    for item in files:
        match = re.match(pattern,item)
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

if __name__ != '__main__':
    filename = scan_for_file()
    if not filename:
        print("[!] Initialization could not find a suitable file")
        print("[i] Entering setup...")
        filename = input("[?] Enter your db name: ")
        filetype = '.*\.cr'
        if not re.match(filetype,filename):
            filename = filename + '.cr'
    conn = sqlite3.connect(filename)
    db = conn.cursor()