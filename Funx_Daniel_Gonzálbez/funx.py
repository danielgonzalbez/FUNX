from flask import Flask, render_template, request
from antlr4 import *
from funxLexer import funxLexer
from funxParser import funxParser
from funxVisitor import funxVisitor


class EvalVisitor(funxVisitor):
    def __init__(self):
        self.symbol_stack = []  # values of local variables
        self.func_dict = {}  # key: name of the function, value: {list of params, function block}
        self.declared_fun = []  # array with names and parameters of declared functions (used in the web)

    def visitRoot(self, ctx):
        l = list(ctx.getChildren())
        res = None
        i = 0
        n = len(l)
        while res is None and i < n:
            res = self.visit(l[i])
            i += 1
        return res

    def visitParam(self, ctx):  # either a value or a variable
        l = list(ctx.getChildren())
        expr_txt = l[0].getText()
        if expr_txt == 'true':
            return True
        if expr_txt == 'false':
            return False
        if 'a' <= expr_txt[0] <= 'z':  # variable
            if len(self.symbol_stack) == 0:  # not inside a function
                raise Exception('Global variables are not permitted')
            else:  # inside a function
                if expr_txt in self.symbol_stack[-1].keys():
                    return self.symbol_stack[-1][expr_txt]
                return 0  # no defined variables are 0 by default
        else:  # value
            return int(expr_txt)  # returned values are always of type int

    def visitOperate(self, ctx):
        l = list(ctx.getChildren())
        op = {'+': lambda x, y: x + y, '-': lambda x, y: x - y,
              '*': lambda x, y: x * y, '//': lambda x, y: x / y,
              '%': lambda x, y: x % y, '^': lambda x, y: x ** y,
              '=': lambda x, y: x == y, '>': lambda x, y: x > y,
              '<': lambda x, y: x < y, '>=': lambda x, y: x >= y,
              '<=': lambda x, y: x <= y, '!=': lambda x, y: x != y,
              'and': lambda x, y: x & y, 'or': lambda x, y: x | y}
        oper1 = self.visit(l[0])
        oper2 = self.visit(l[2])
        if (l[1].getText() == '/' or l[1].getText() == '%') and oper2 == 0:
            raise Exception('Division or modulo by zero not permitted')
        f = op[l[1].getText()]
        return f(oper1, oper2)

    def visitAssign(self, ctx):
        l = list(ctx.getChildren())
        var = l[0].getText()
        self.symbol_stack[-1][var] = self.visit(l[2])  # variables are always of type int

    def visitIf(self, ctx):
        l = list(ctx.getChildren())
        if(self.visit(l[1])):
            return (self.visit(l[3]))

    def visitIfelse(self, ctx):
        l = list(ctx.getChildren())
        if self.visit(l[1]):
            return (self.visit(l[3]))
        else:
            return (self.visit(l[7]))

    def visitWhile(self, ctx):
        l = list(ctx.getChildren())
        while(self.visit(l[1])):
            res = self.visit(l[3])
            if res is not None:  # if there is a return, the loop ends
                return res

    def visitDeclare_function(self, ctx):  # Declare a function
        l = list(ctx.getChildren())
        id_fun = l[0].getText()
        if id_fun in self.func_dict.keys():
            raise Exception('The function with name %s already exists.' % id_fun)
        list_params = []
        i = 1
        new_fun = id_fun
        while(l[i].getText() != '{'):  # get the formal parameters
            new_param = l[i].getText()
            if new_param in list_params:
                raise Exception('More than one parameter has been defined with the name %s.' % new_param)
            else:
                list_params.append(new_param)
                new_fun += ' ' + new_param
            i = i + 1
        ctx_block = l[i+1]  # instructions
        self.func_dict[id_fun] = {'list_params': list_params, 'ctx_block': ctx_block}
        self.declared_fun.append(new_fun)

    def visitCall_fun(self, ctx):
        l = list(ctx.getChildren())
        id_fun = l[0].getText()
        if id_fun in self.func_dict.keys():  # check if the called function exists
            list_params_fun = self.func_dict[id_fun]['list_params']
            if len(list_params_fun) != len(l[1:]):
                raise Exception('Got: %i arguments. Expected: %i arguments.' % (len(l[1:]), len(list_params_fun)))
            symbol_dict = {}  # matches the given values with the parameters of the function
            i = 0
            for elem in l[1:]:  # each elem is a given value for the params
                value_param = self.visit(elem)
                symbol_dict[list_params_fun[i]] = value_param
                i = i + 1
            self.symbol_stack.append(symbol_dict)  # new local variables with new values
            list_inst = self.func_dict[id_fun]['ctx_block']
            res = self.visit(list_inst)
            self.symbol_stack.pop()  # the current local variables are no longer needed
            return res
        else:
            raise Exception('The function with name %s has not been defined.' % id_fun)

    def visitRet_expression(self, ctx):
        l = list(ctx.getChildren())
        return(self.visit(l[0]))

    def visitParenthesis(self, ctx):
        l = list(ctx.getChildren())
        return(self.visit(l[1]))  # ignore the parenthesis

    def visitBloc(self, ctx):
        l = list(ctx.getChildren())  # list of instructions
        res = None
        i = 0
        n = len(l)
        while res is None and i < n:  # iterate through instructions
            res = self.visit(l[i])
            i += 1
        return res

app = Flask(__name__)

visitor = EvalVisitor()

inputs_results = []  # list of 5 dictionaries with the last 5 inputs and results
num_result = 1  # idx of the next input


@app.route('/')  # welcome page
def index():
    return render_template('index.html')


@app.route('/begin', methods=['GET'])  # initialize page
def process_no_input():
    return render_template('result.html', form_data=[[], []])


@app.route('/result', methods=['POST'])  # update page
def process_input():
    text = request.form['input_text']
    input_stream = InputStream(text)
    lexer = funxLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = funxParser(token_stream)
    tree = parser.root()
    try:
        res = visitor.visit(tree)
    except Exception as e:
        res = 'ERROR: ' + str(e)
    if len(inputs_results) == 5:  # just show the last 5 results
        inputs_results.pop(-5)
    global num_result
    inputs_results.append({"input": text, "result": res, "idx": num_result})
    num_result += 1
    return render_template('result.html', form_data=[reversed(inputs_results), visitor.declared_fun])

if __name__ == "__main__":
    app.run(debug=True)
