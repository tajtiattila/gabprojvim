Project manager script by Dorka Gábor
Minor additons by Attila Tajti


:map <unique> <LocalLeader>pi :python import sys<CR>:python sys.argv="init".split()<CR>:pyfile $VIM/vimfiles/plugin/vimproject.py<CR>
:map <unique> <LocalLeader>pe :python import sys<CR>:python sys.argv="enter".split()<CR>:pyfile $VIM/vimfiles/plugin/vimproject.py<CR>
:map <unique> <LocalLeader>pg :python import sys<CR>:python sys.argv="grep case part".split()<CR>:pyfile $VIM/vimfiles/plugin/vimproject.py<CR>
:map <unique> <LocalLeader>pG :python import sys<CR>:python sys.argv="grep nocase part".split()<CR>:pyfile $VIM/vimfiles/plugin/vimproject.py<CR>
:map <unique> <LocalLeader>ph :python import sys<CR>:python sys.argv="grep case whole".split()<CR>:pyfile $VIM/vimfiles/plugin/vimproject.py<CR>
:map <unique> <LocalLeader>pH :python import sys<CR>:python sys.argv="grep nocase whole".split()<CR>:pyfile $VIM/vimfiles/plugin/vimproject.py<CR>
:map <unique> <LocalLeader>pa :python import sys<CR>:python sys.argv="alternate".split()<CR>:pyfile $VIM/vimfiles/plugin/vimproject.py<CR>
:map <unique> <LocalLeader>pr :python import sys<CR>:python sys.argv="replace".split()<CR>:pyfile $VIM/vimfiles/plugin/vimproject.py<CR>

