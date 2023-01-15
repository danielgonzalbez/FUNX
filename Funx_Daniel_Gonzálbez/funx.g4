grammar funx ;

root : declare_function* expr? EOF; 

declare_function : FUN VAR* '{' bloc '}' ;

expr : FUN expr* # call_fun
    | <assoc=right> expr '^' expr # operate
    | expr ('*' | '/' | '%') expr # operate
    | expr ('+' | '-') expr # operate
    | NUM # param 
    | VAR # param
    | expr '=' expr # operate
    | expr '>' expr # operate
    | expr '<' expr # operate
    | expr '>=' expr # operate
    | expr '<=' expr # operate
    | expr '!=' expr # operate
    | expr 'and' expr # operate
    | expr 'or' expr # operate
    | '(' expr ')' # parenthesis
    ;

instr : VAR '<-' expr # assign
      | 'if' expr '{' bloc '}' # if
      | 'if' expr '{' bloc '}' 'else' '{' bloc '}' # ifelse
      | 'while' expr '{' bloc '}' # while
      | expr # ret_expression
      ;

bloc : instr+ ;


VAR : [a-z][a-zA-Z0-9]* ;
NUM : [0-9]+ ;
FUN : [A-Z][a-zA-Z0-9]* ;




WS : [ \n]+ -> skip ;


