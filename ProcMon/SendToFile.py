

def print_to_file(proclist):
	for proc in proclist:  # iterate each tuple
		ex_states = ("LISTEN", None)
		if not proc[9]:
			raddr = "N/A"
			rport = "N/A"
		else:
			raddr = proc[9][0]
			rport = proc[9][1]

		print(

				"""Process ID -> {pid}
				***************************
				Name ---------------------> {proc_name}
				File Path ================> {file_path}
				File Sha256 Hash ---------> {hash}
				Working Dir ==============> {cwd}
				Status -------------------> {status}
				Running Under User =======> {perms}
				Socket State -------------> {state}
				Listening Address ========> {laddr}
				Local Port ---------------> {lport}
				Remote Address ===========> {raddr}
				Remote Port --------------> {rport}
				""".format(pid=proc[0], proc_name=proc[1], file_path=proc[2], hash=proc[3], cwd=proc[5], status=proc[4],
           perms=proc[6], laddr=proc[8][0], lport=proc[8][1], raddr=raddr, rport=rport, state=proc[10]))
		if len(proc[11]) != 0:
			children = proc[11]
			for child in children:
				print(
						""" \tChild ID -> {pid}
							***************************
							Name ---------------------> {ch_name}
							File Path ================> {ch_exe}
							File Sha256 Hash ---------> {hash}
						""".format(pid=child[0], ch_name=child[1], ch_exe=child[2], hash=child[3]))


			# print("""
			# {pid}     {status}    {perms}     {state}     {laddr}     {lport}     {raddr}     {rport}     {file_path}
			# """.format(pid=proc[0],proc_name=proc[1],file_path=proc[2],hash=proc[3],status=proc[4],
			# 	           perms=proc[5],laddr=proc[7][0],lport=proc[7][1],raddr=raddr,rport=rport,state=proc[9]))
			# sys.exit(0)

