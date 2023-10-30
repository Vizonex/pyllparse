# pyllparse
A parody of library of llparse. Original version was written in typescript by Indutny

I take no credit for the orginal work done by indutny and I was originally very nervous about making 
this python library that I made public... 

Links to the original library 
- https://llparse.org
- https://github.com/nodejs/llparse

Unlike the typescript library all 3 of llparse's libraries were combined in this version of the code for the sake of portability... 
I ended up mentioning how I did this a while back and I also had a concept for a C parser as well but I just didn't like it and I ended up using this instead but I also learned typescript as a bonus and It was alot of fun for me. I don't plan to make this into a real pypi library yet but I also didn't want to take away from the magic of the original source code that I borrowed from...

# Why Did I Translate llparse to python?
- I wanted to work with a langauge I was more familiar with
- Better educate myself and others on how these great libraries like llhttp are made
- Write faster C code that could do more than just a simple split function or a regex...
- Make it easy for me or someone else to find a problem and solve it in typescript after testing it in python
- Typescript takes 2 commands to run a script with node-js it while python only takes one cutting the time required tremendously...
- The orginal project was MIT licensed.
- I wanted to write my own C Parsering tool with llhttp styled callbacks of my own using a language I was the most comfortable with using.
- I didn't like __Lemon Parser__ or __Yacc__ all that much and a good ide for handling them in Visual Studio Code with error checking to my knowlegde does not exist.
- The closest thing I got to what I wanted was a project named __NMFU__ shorthand for no memory for you and even I had problems with writing things using that library...

This was the Code that inspired me to try and make a new pyi writer branch for cython and if it wasn't for llhttp 
existing as well as it's magical experience I would've never done what I did.

Unlike llparse in typescript, this version has more integrated and experimental features like automatically building the api seen in llhttp and 
I've added a few other things like the dot compiler from llparse_dot and I also made a brand new cython compiler 
for it making easy and simple to make pxd files to port your projects to cython 

# TODOS
- Make a script to compile projects to node-js by making a .gyp file for them...
- Make a script for compiling C files to `.lib` and `.dll` extensions as well as the `.a / .so` files seen on Linux and Apple Systems...
- Add in additional debuggers
- Make a youtube tutorial on how to use this library on Vizonex Builds
- Release pypi packages
- Build an enum compiler like seen in llhttp
- Implement llvm bytecode and js outputs if I have the time for it.
 
