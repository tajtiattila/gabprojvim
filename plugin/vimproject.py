#!/usr/bin/env python
# vim: noexpandtab tabstop=4 shiftwidth=4
###################################################################################################
# TODO: taglist to quickfix window
#
import string
import sys
import os
import re
import subprocess
import ConfigParser
import fnmatch
try:
	import vim
except:
	pass

# these values can be overridden in either:
#   ~/.vimproj-config
# or
#   $VIM/vimfiles/plugin/.vimproj-config
VIMPROJECT_BASE = ".vimproject"
VIMPROJECT_CFG_NAME = VIMPROJECT_BASE + ".cfg"
VIMPROJECT_PATH_START_POS = 80
VIMPROJECT_CTAGS_MASK_LIST = [ "*.*" ]
VIMPROJECT_CTAGS_CMD = "ctags"
VIMPROJECT_CTAGS_DB_NAME = VIMPROJECT_BASE + ".tags"
VIMPROJECT_CSCOPE_MASK_LIST = [ "*.c", "*.h", "*.cpp", "*.hpp" ]
VIMPROJECT_CSCOPE_CMD = "mlcscope"
VIMPROJECT_CSCOPE_DB_NAME = VIMPROJECT_BASE + ".cscope.out"
VIMPROJECT_EXPLORER_LIST_NAME = VIMPROJECT_BASE + "_explorer_list.txt"
VIMPROJECT_GREP_LIST_NAME = VIMPROJECT_BASE + "_grep_list.txt"
VIMPROJECT_TEMP_LIST_NAME = VIMPROJECT_BASE + "_temp_list.txt"
VIMPROJECT_EXTERNAL_GREP = "grep -r -n %$ ."

try:
	execfile(os.path.join(os.environ['HOME'], '.vimproj-config'))
except:
	try:
		execfile(os.path.join(os.environ['VIM'], 'vimfiles/plugin', '.vimproj-config'))
	except:
		pass

###################################################################################################
class project_t():


	#############################################################################
	WORD_LETTERS = '_' + string.ascii_letters + string.digits
	GLOBAL_PREV_BUFFER_NAME = 'g:vimproject_prev_buffer_name'


	#############################################################################
	def do(self, argv):
		command = argv[0]
		arg_list = argv[1:]
		# do commands
		if command=='load':
			pass
		elif command=='init':
			self.do_init()
		elif command=='enter':
			self.do_enter()
		elif command=='exit':
			self.do_exit()
		elif command=='select':
			self.do_select()
		elif command=='grep':
			self.do_grep(arg_list)
		elif command=='alternate':
			self.do_alternate()
		elif command=='replace':
			self.do_replace()
		elif command=='cscope':
			self.do_cscope(arg_list)
		else:
			sys.stderr.write("invalid command '%s'\n" % command)


	#############################################################################
	def do_init(self):
		# read cfg
		self.cfg_parser = ConfigParser.SafeConfigParser()
		self.cfg_parser.read(VIMPROJECT_CFG_NAME)
		# read options
		use_cscope = self.get_option('cscope', 'no') == 'yes'
		# read dirs
		dirs = self.get_option('dirs', '')
		dirs_list = dirs.split('\n')
		# get file masks
		files = self.get_option('files', '')
		files_list = files.split('\n')
		mask_list = []
		for mask in files_list:
			if len(mask)==0 or mask[0]=='#':
				continue
			if len(mask)<2:
				sys.stderr.write("mask is too short '%s'\n" % mask)
				return
			if mask[0]=='+' or mask[0]=='-':
				op = mask[0]
				mask = mask[1:]
			else:
				sys.stderr.write("invalid mask prefix at '%s'\n" % mask)
				return
			dot = mask.find('.')!=-1
			star = mask.find('*')!=-1
			mask_list.append((op, dot, star, mask))
		# init lists
		explorer_list = ''
		grep_list = ''
		ctags_list = ''
		cscope_list = ''
		# pre cleanup
		self.try_remove_file(VIMPROJECT_EXPLORER_LIST_NAME)
		self.try_remove_file(VIMPROJECT_GREP_LIST_NAME)
		self.try_remove_file(VIMPROJECT_TEMP_LIST_NAME)
		self.try_remove_file(VIMPROJECT_CTAGS_DB_NAME)
		self.try_remove_file(VIMPROJECT_CSCOPE_DB_NAME)
		# walk all dirs and collect files
		for dir_name in dirs_list:
			if len(dir_name)==0:
				continue
			dir_space_count = len(os.path.abspath(dir_name).split('\\')) * 2
			for root_name, dir_name_list, file_name_list in os.walk(dir_name):
				norm_root_name = os.path.normpath(root_name)
				space_count = len(os.path.abspath(root_name).split('\\')) * 2 - dir_space_count + 2
				explorer_appended = False
				for file_name in file_name_list:
					# decide if the file is needed into project
					full_file_name = os.path.join(norm_root_name, file_name)
					abs_file_name = os.path.abspath(os.path.join(norm_root_name, file_name))
					needed = False
					for op, dot, star, mask in mask_list:
						if (not needed and op=='+') or (needed and op=='-'):
							# pattern
							if star:
								if not fnmatch.fnmatch(full_file_name,mask):
									continue
							# find
							else:
								find_pos = full_file_name.find(mask)
								if find_pos==-1:
									continue
								if dot and find_pos!=len(full_file_name)-len(mask):
									continue
							needed = not needed
					# add file name to various lists
					if needed:
						explorer_list += ' '*space_count + file_name + ' '*(VIMPROJECT_PATH_START_POS-space_count-len(file_name)) + abs_file_name + '\n'
						explorer_appended = True
						grep_list += abs_file_name.replace('\\','/') + '\0'
						for ctags_mask in VIMPROJECT_CTAGS_MASK_LIST:
							if fnmatch.fnmatch(file_name,ctags_mask):
								ctags_list += abs_file_name + '\n'
								break
						if use_cscope:
							for cscope_mask in VIMPROJECT_CSCOPE_MASK_LIST:
								if fnmatch.fnmatch(file_name,cscope_mask):
									cscope_list += abs_file_name + '\n'
									break
				if explorer_appended:
					explorer_list += '-' * (VIMPROJECT_PATH_START_POS + 20) + '\n'
		# write simple lists
		self.write_list(explorer_list, VIMPROJECT_EXPLORER_LIST_NAME)
		self.write_list(grep_list, VIMPROJECT_GREP_LIST_NAME)
		# generate ctags db
		if len(VIMPROJECT_CTAGS_CMD)>0:
			self.write_list(ctags_list, VIMPROJECT_TEMP_LIST_NAME)
			retcode, output = self.execute_command(VIMPROJECT_CTAGS_CMD + ' -L ' + VIMPROJECT_TEMP_LIST_NAME + ' -f ' + VIMPROJECT_CTAGS_DB_NAME)
			if retcode!=0:
				sys.stderr.write('ctags exec error:\n' + output)
				return
		# generate cscope db
		if use_cscope:
			if len(VIMPROJECT_CSCOPE_CMD)>0:
				self.write_list(cscope_list, VIMPROJECT_TEMP_LIST_NAME)
				retcode, output = self.execute_command(VIMPROJECT_CSCOPE_CMD + ' -b -i ' + VIMPROJECT_TEMP_LIST_NAME + ' -f ' + VIMPROJECT_CSCOPE_DB_NAME)
				if retcode!=0:
					sys.stderr.write('cscope exec error:\n' + output)
					return
		# post cleanup
		self.try_remove_file(VIMPROJECT_TEMP_LIST_NAME)


	#############################################################################
	def do_enter(self):
		# get the name of buf before we change current buffer
		buf_full_name = vim.current.buffer.name
		if buf_full_name is None:
			buf_full_name = ''
		vim.command("let %s='%s'" % (self.GLOBAL_PREV_BUFFER_NAME, buf_full_name))
		# open list file
		vim.command(':view ' + VIMPROJECT_EXPLORER_LIST_NAME)
		vim.command(':setlocal nomodifiable cursorline nowrap')
		vim.current.window.cursor = (1, 0)
		# try to jump to the name of the file which was in the previous buffer
		if not buf_full_name is None:
			buf_full_name = buf_full_name.lower()
			line_idx = 1
			for line in vim.current.buffer[:]:
				if line[VIMPROJECT_PATH_START_POS:].lower()==buf_full_name:
					vim.current.window.cursor = (line_idx, 0)
					break
				line_idx += 1
		# remap esc, space, enter for this buffer
		vim.command('noremap <buffer> <silent> <Esc> :python project.do_exit()<CR>')
		vim.command('map <buffer> <silent> <Space> <Esc>')
		vim.command('noremap <buffer> <silent> <CR> :python project.do_select()<CR>')


	#############################################################################
	def do_exit(self):
		# close explorer window
		vim.command(':bwipeout! ' + VIMPROJECT_EXPLORER_LIST_NAME)


	#############################################################################
	def do_select(self):
		# open the file by name
		if vim.current.line[0]=='-':
			return
		# set previous buffer so alternate will work
		prev_buf_full_name = vim.eval(self.GLOBAL_PREV_BUFFER_NAME)
		path = vim.current.line[VIMPROJECT_PATH_START_POS:]
		if prev_buf_full_name!='' and prev_buf_full_name!=path:
			vim.command(':edit ' + prev_buf_full_name)
		vim.command(':edit ' + path)
		# quit explorer
		self.do_exit()


	#############################################################################
	def do_grep(self, arg_list, redir=''):
		if not arg_list:
			return
		word = arg_list[-1]
		arg_list = arg_list[:-1]
		# do the grep
		retcode, output = self.execute_command('cat ' +
				VIMPROJECT_GREP_LIST_NAME+' | xargs -0 -r -n 100 grep ' + ' '.join(arg_list) +
				' -n ' + word + redir)
		if not redir:
			sys.stdout.write(output)
		return retcode


	#############################################################################
	def do_grepcursor(self, arg_list):
		# get the word under cursor
		word = self.get_word_under_cursor()
		if word is None:
			return
		self.do_grep(arg_list + [word], ' >' + VIMPROJECT_TEMP_LIST_NAME + ' 2>&1')
		# open grep output in quickfix window
		vim.command(':cfile ' + VIMPROJECT_TEMP_LIST_NAME)


	#############################################################################
	def do_xgrep(self, arg_list):
		if os.path.exists(VIMPROJECT_GREP_LIST_NAME):
			self.do_grep(arg_list)
			return

		if hasattr(VIMPROJECT_EXTERNAL_GREP, '__call__'):
			VIMPROJECT_EXTERNAL_GREP(arg_list)
		elif isinstance(VIMPROJECT_EXTERNAL_GREP, basestring):
			cmd = VIMPROJECT_EXTERNAL_GREP.replace('%$', ' '.join(arg_list))
			retcode, output = self.execute_command(cmd)
			if retcode!=0:
				sys.stderr.write(cmd+'\ncommand returned with error:\n'+output)
				return
			sys.stdout.write(output)
		else:
			sys.stderr.write('unrecognisable VIMPROJECT_EXTERNAL_GREP, should be function or string\n')


	#############################################################################
	def do_alternate(self):
		# get the name of buf
		buf_full_name = vim.current.buffer.name
		if buf_full_name is None:
			return
		buf_full_name = buf_full_name.lower()
		# check project entries
		buf_name, buf_ext = os.path.splitext(buf_full_name)
		buf_short_name = os.path.split(buf_name)[1]
		cur_idx = 0
		idx = 0
		name_ext_list = []
		name_list = []
		for line in file(VIMPROJECT_EXPLORER_LIST_NAME):
			idx += 1
			line_full_name = line[VIMPROJECT_PATH_START_POS:].strip().lower()
			if line_full_name==buf_full_name:
				cur_idx = idx
				continue
			line_name, line_ext = os.path.splitext(line_full_name)
			if line_name==buf_name:
				name_ext_list.append([idx, line_full_name])
				continue
			line_short_name = os.path.split(line_name)[1]
			if line_short_name==buf_short_name:
				name_list.append([idx, line_full_name])
				continue
		# look for closest match
		if len(name_ext_list)>0:
			search_list = name_ext_list
		elif len(name_list)>0:
			search_list = name_list
		else:
			return
		min_idx_dist = 99999999
		min_idx_name = ''
		for idx, name in search_list:
			idxdist = abs(cur_idx - idx)
			if idxdist<min_idx_dist:
				min_idx_dist = idxdist
				min_idx_name = name
		# switch to closest
		vim.command(':edit '+min_idx_name)


	#############################################################################
	def do_replace(self):
		# TODO: whole word only?
		# get word pair under cursor
		word0, word1 = self.get_word_pair_under_cursor()
		if word0 is None:
			return
		# do the grep
		retcode, output = self.execute_command('cat ' + VIMPROJECT_GREP_LIST_NAME + ' | xargs -0 -r -n 100 grep -n ' + word0 +
													' >' + VIMPROJECT_TEMP_LIST_NAME + ' 2>&1')
		vim.command(':cfile ' + VIMPROJECT_TEMP_LIST_NAME)
		if len(vim.current.line)==0:
			return
		# replace words in lines
		replace_count = len(vim.current.buffer)
		subst_cmd = '.s/'+word0+'/'+word1+'/g'
		try:
			vim.command(':cc')
		except vim.error:
			return
		vim.command(subst_cmd)
		for idx in range(replace_count-1):
			try:
				vim.command(':cn')
			except vim.error:
				break
			vim.command(subst_cmd)


	#############################################################################
	def do_cscope(self, arg_list):
		# consts
		cscope_cmd_names = ['symbol(s)', 'definition(s)', 'reference(s)']
		cscope_cmd_codes = ['0', '1', '3']
		# set args
		if len(arg_list)!=1:
			sys.stderr.write('cscope requires 1 argument\n')
			return
		arg = arg_list[0]
		if arg=='symbol':
			cmd_idx = 0
		elif arg=='definition':
			cmd_idx = 1
		elif arg=='reference':
			cmd_idx = 2
		else:
			sys.stderr.write("invalid cscope argument: '%s'\n" % arg)
			return
		# get the word under cursor
		word = self.get_word_under_cursor()
		if word is None:
			return
		# start the output file
		tempfile = file(VIMPROJECT_TEMP_LIST_NAME, 'wt')
		tempfile.write('*** %s %s ***\n' % (word, cscope_cmd_names[cmd_idx]))
		cscope_cmd = cscope_cmd_codes[cmd_idx]
		retcode, output = self.execute_command(VIMPROJECT_CSCOPE_CMD + ' -d -L -f ' + VIMPROJECT_CSCOPE_DB_NAME +
												' -' + cscope_cmd + ' ' + word + ' > ' + VIMPROJECT_TEMP_LIST_NAME, False)
		if retcode!=0:
			sys.stderr.write('cscope returned with error:\n'+output)
			return
		line_list = output.split('\n')
		line_re = re.compile(r'(?P<filename>[^ ]*) [^ ]* (?P<linenum>\d*) (?P<line>.*)')
		for line in line_list:
			if len(line)==0:
				continue
			match_obj = line_re.match(line)
			if match_obj is None:
				sys.stderr.write('can\'t process cscope output line:\n'+line)
				return
			tempfile.write('%s:%s:%s\n' % (match_obj.group('filename'), match_obj.group('linenum'), match_obj.group('line')))
		tempfile = None
		# open tag output in quickfix window
		vim.command(':cfile '+VIMPROJECT_TEMP_LIST_NAME)


	#############################################################################
	def get_option(self, key, def_value):
		try:
			value = self.cfg_parser.get('project', key)
			return value
		except ConfigParser.NoOptionError:
			return def_value


	#############################################################################
	def try_remove_file(self, name):
		try:
			os.remove(name)
		except Exception:
			pass


	#############################################################################
	def write_list(self, wlist, name):
		list_file = file(name, 'wt')
		list_file.write(wlist)
		list_file.close()


	#############################################################################
	def get_word_under_cursor(self):
		line = vim.current.line
		linei0 = linei1 = vim.current.window.cursor[1]
		while linei0 > 0 and self.WORD_LETTERS.find(line[linei0-1]) != -1:
			linei0 -= 1
		while linei1 < len(line) and self.WORD_LETTERS.find(line[linei1]) != -1:
			linei1 += 1
		word = line[linei0 : linei1]
		if len(word)==0:
			sys.stderr.write('can\'t detect word under cursor')
			return None
		return word


	#############################################################################
	def get_word_pair_under_cursor(self):
		line = vim.current.line
		linei0 = linei1 = vim.current.window.cursor[1]
		while linei0 > 0 and self.WORD_LETTERS.find(line[linei0-1]) != -1:
			linei0 -= 1
		while linei1 < len(line) and self.WORD_LETTERS.find(line[linei1]) != -1:
			linei1 += 1
		word0 = line[linei0 : linei1]
		linei0 = linei1 + 1
		linei1 += 1
		while linei1 < len(line) and self.WORD_LETTERS.find(line[linei1]) != -1:
			linei1 += 1
		word1 = line[linei0 : linei1]
		if len(word0)==0 or len(word1)==0:
			sys.stderr.write('can\'t detect word(s) to replace')
			return None, None
		return word0, word1


	#############################################################################
	def execute_command(self, command, in_shell=True):
		retcode = -1
		output = ''
		try:
			p = subprocess.Popen(command, shell=in_shell, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
			while True:
				output += p.stdout.read()
				retcode = p.poll()
				if not retcode is None:
					break
		except Exception, inst:
			output += 'Exception ' + type(inst) + '\n' + str(inst) + '\n'
		return retcode, output


###################################################################################################
project = project_t()

if __name__ == "__main__":
	v = sys.argv[1:]
	if v and v[0] == 'xgrep':
		project.do_xgrep(v[1:])
