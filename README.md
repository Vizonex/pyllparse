# pyllparse
A parody of llparse like pyppeteer that I made a couple months ago that I never got around to sharing or uploading.  Original was in typescript by Indutny

I have no plans on resumig this anytime soon. I did it more as a educational thing and I would've just gone ahead and dumped my code into a gist but that would be extremely big since there's three libraries involved with making llparse work alone. Translating it was difficult and there may be a couple of minor hiccups that I did not catch yet that do not mimic the same behaviors as llparse itself... I was also going to make a pxd compiler for this in the future but will have to wait and see. 

I take no credit for the orginal work done by indutny and I was very nervous about making this public... 

Links to the original library 
- https://llparse.org
- https://github.com/nodejs/llparse

Unlike the typescript library all 3 of llparse's library were combined here for the sake of portability... 
I ended up mentioning how I did this a while back and I also had a concept for a C parser as well but I just didn't like it and I ended up using this instead but I also learned typescript as a bonus and It was alot of fun for me. I don't plan to make this into a real library yet but I didn't want to take away from the magic of the original source that I borrowed from...

This was the Code that inspired me to tackle cython and enable for cython to likely have a new pyi compiler branch if it wasn't for llhttp existing and it's magical experience I would've never done what I did.


Unlike llparse this has deeply integrated features like building the api seen in llhttp and I've added a few other things like the dot compiler and also a brand new cython compiler for making easy and simple pxd files for your projects to cython 

# TODOS
- Make a script to compile projects to node-js by making a .gyp file for them...
- Make a script for compiling C files to `.lib` and `.dll` extensions as well as the `.a / .so` files seen on Linux and Apple Systems...
- Add in additional debuggers
- Make a youtube tutorial on how to use this library on Vizonex Builds
- Release pypi packages

