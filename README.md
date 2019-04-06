# Rattled Python
Rattled Python is a programming language I have set out to create
in attempts to decrease the amount of typing a programmer actually
has to do. The whole idea behind it was to decrease the amount of
letters to be typed for simple functions as well as programming
identifiers. Instead of typing out 'print("")' in python, in Rattled
Python you can type 'pr ""' which would do the same thing as a print()
function in python. Rattled Python was also designed for readability,
which is why brackets ({}) have been required for containing the bodies of
if statements, for, and while loops. I will admit that Java was my
first language and I always did love brackets. Loops were designed with
simplicity in mind at best. Rather than having to increment variables
within the loop declaration, if the variable within the loop has not
been previously defined, then it will be automatically set to 0 and
increment as the loop passes through its body. This of course will not
work so well if you have a loop like 'while i > 5' in which the variable
i should be previously defined.
# Code Preview
```
age = 21
name = 'Jared'
bool = boo('TRUE')
`This is a comment in Rattled`
for i < 5 {
    pr 'Example of a for loop in Rattled ' + i
}

while i < 5 {
    pr 'Example of a while loop in Rattled ' + i
}

if bool {
    pr "My name is " + name + " and I am " + age + " years old";
}
```
# TODO List
[x] Lexer splits up source code into tokens by spaces

[ ] Code actually runs the functions

[ ] Spaces get ignored by lexer

[ ] Multi-line variable declaration by keeping variable values in parenthesis

[ ] Keywords (if, for, while) ignore spacing and parenthesis when parsing
their bodies and conditionals
# Installation
TBD
# Documentation
TBD