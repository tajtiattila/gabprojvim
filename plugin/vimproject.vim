"=============================================================================
" File:        vimproject.vim
" Author:      Attila Tajti
" Version:     0.1
"=============================================================================
" See documentation in accompanying help file
" You may use this code in whatever way you see fit.

" Do not load if we have already been loaded.
if exists('loaded_vimproject') || &cp
  finish
endif
if (v:progname == "ex")
   finish
endif

" Default configuration
let s:BASE = ".vimproject"
let g:VIMPROJECT_CFG_NAME = s:BASE . ".cfg"
let g:VIMPROJECT_PATH_START_POS = 80
let g:VIMPROJECT_CTAGS_MASKS = "*.*"
let g:VIMPROJECT_CTAGS_CMD = "ctags"
let g:VIMPROJECT_CTAGS_DB_NAME = s:BASE . ".tags"
let g:VIMPROJECT_CSCOPE_MASKS = "*.c *.h *.cpp *.hpp"
let g:VIMPROJECT_CSCOPE_CMD = "mlcscope"
let g:VIMPROJECT_CSCOPE_DB_NAME = s:BASE . ".cscope.out"
let g:VIMPROJECT_EXPLORER_LIST_NAME = s:BASE . "_explorer_list.txt"
let g:VIMPROJECT_GREP_LIST_NAME = s:BASE . "_grep_list.txt"
let g:VIMPROJECT_TEMP_LIST_NAME = s:BASE . "_temp_list.txt"
let g:VIMPROJECT_EXTERNAL_GREP = "grep -r -n %$ ."
let g:VIMPROJECT_PATH_SEP = ''
let g:VIMPROJECT_RESULTFILECMD = ":cfile <filename>\n:botright copen"

" Find ourselves (the python file) in the runtime
let s:PyName = "vimproject.py"
let s:PyPath = $VIMPROJDEVDIR
for dir in split(&runtimepath, ',')
	let dirpath = dir."/plugin/"
	if filereadable(dirpath.s:PyName)
		let s:PyPath = dirpath
		break
	endif
endfor
let s:PyPath .= "/".s:PyName

" (re)load python script (after edit)
command! ProjLoad   silent execute ":pyfile ".s:PyPath

" initialize project
command! ProjInit   silent python project.do_init()

" enter project (show files)
command! ProjEnter  silent python project.do_enter()

" grep
command! ProjGrep   silent python project.do_grepcursor("".split())
command! ProjGrepi  silent python project.do_grepcursor("-i".split())
command! ProjGrepw  silent python project.do_grepcursor("-w".split())
command! ProjGrepiw silent python project.do_grepcursor("-i -w".split())

" switch to alternate file (eg. h <-> cpp)
command! ProjAlt    silent python project.do_alternate()
"
" search&replace w/ words under cursor
command! ProjRepl   silent python project.do_replace()

command! -nargs=* Grep silent python project.do_grepargs(<f-args>)

:ProjLoad

:map <unique> <LocalLeader>pi :ProjInit<CR>
:map <unique> <LocalLeader>pe :ProjEnter<CR>
:map <unique> <LocalLeader>pg :ProjGrep<CR>
:map <unique> <LocalLeader>pG :ProjGrepi<CR>
:map <unique> <LocalLeader>ph :ProjGrepw<CR>
:map <unique> <LocalLeader>pH :ProjGrepiw<CR>
:map <unique> <LocalLeader>pa :ProjAlt<CR>
:map <unique> <LocalLeader>pr :ProjRepl<CR>

" use this as grepprg
"let g:VimProjGrepPrg = s:PyPath." xgrep "
":let &grepprg=s:PyPath." xgrep "

