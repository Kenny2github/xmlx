import re #wow this is literally the only module used 0.0

class Element(): #element class, here we go!
    def __str__(self): #string representation
        return '<'+self.name+' '*int(bool(self.attrib))+' '.join([k+'="'+v+'"' for k, v in self.attrib.items()[:3]])+'>...</'+self.name+' at '+hex(id(self))+'>' #i.e. <p>...</p at mem>
    __repr__ = __str__ #repr = str duh
    def __hash__(self):
        '''Hash of the element.

The return value is the hash of a combination of
the element's name, text, and attributes, so the
hashes of two elements with the same name, text,
and attributes will compare equal.'''
        return hash(tuple(self.attrib.items()) + (self.name, self.text))
    __eq__ = lambda s, o: hash(s) == hash(o)
    def __init__(self, text, **xtrs): #INIT
        '''Initialize the element from a string.

Suppose we have an element string:
'<p class="test">paragraph <b>bold</b></p>'

self.name - the name of the element, "p" for this case

self.attrib - the attributes of the element.
{"class":"test"} for this case

self.content - equivalent to JavaScript innerHTML.
"paragraph <b>bold</b>" for this case

self.text - equivalent to JavaScript outerHTML.
'<p class="test">paragraph <b>bold</b></p>' for this case

self.children - a list of sub-elements in this element.
[<b>...</b>] for this case

self.childrendict - a dictionary of sub-elements in the
format "name":<element>. {"b":<b>...</b>} for this case'''
        assert type(text) in [str, unicode], "expected str, got " + type(text).__name__ #assert str or unicode
        text = re.sub(r'<[!\?].*?>', '', text, flags=re.S).strip() #remove all SGML weird stuff and comments and make sure we can match it
        assert bool(re.match(r'((?:<([^<>/]*?)(?: [^<>]*?)?>.*?</\2>)|(?:<[^<>/]*?/>))', text, re.S)), "text does not match element format" #assert that this is an element
        if re.match(r'<[^<>/]*?/>', text, re.S): #if the element is <foo/> and not <foo>bar</foo>
            self.name = re.match('<([^<>/]*?)(?: [^<>]*?)?/>', text, re.S).group(1) #get the name
            self.attrib = {} #no attributes yet
            for m in re.finditer(' (?P<name>[^<>/]*?)=(?P<value>(?:[\'"][^<>]*?[\'"])|(?:[^<>/\'"]*))', re.search('<[^<>/]*?((?: [^<>/]*?)*?)?/>', text, re.S).group(1), flags=re.S): #for every attrib="value"
                self.attrib[m.group('name')] = m.group('value') #attrib=value
            self.content = '' #since this is <foo/> there's no content
            self.text = text #outerHTML
            self.pre = xtrs.get('pre', '') #text before us, if we're a child element
            self.post = xtrs.get('post', '') #text after us, if we're a child element
            self._updateChildren() #just to be consistent
        else: #it's <foo>bar</foo> after all
            self.name = re.match(r'<([^<>/]*?)(?: [^<>]*?)?>.*?</\1>', text, re.S).group(1) #get the name
            self.attrib = {} #no attributes yet
            for m in re.finditer(' (?P<name>[^<>/]*?)=(?P<value>(?:[\'"][^<>]*?[\'"])|(?:[^<>/\'"]*))', re.search('<[^<>/]*?((?: [^<>]*?)*?)>', text, flags=re.S).group(1), flags=re.S): #for every attrib="value"
                self.attrib[m.group('name')] = m.group('value') #attrib=value
            self.content = re.match(r'<([^<>/]*?)(?: [^<>]*?)?>(?P<text>.*?)</\1>', text, flags=re.S).group('text') #get the content
            self.text = text #outerHTML
            self.pre = xtrs.get('pre', '') #text before us, if we're a child element
            self.post = xtrs.get('post', '') #text after us, if we're a child element
            self._updateChildren()
    def _updateChildren(self):
        self.children = [] #no children yet
        for m in re.findall(r'([^<>]*)((?:<([^<>/]*?)(?: [^<>]*?)?>.*?</\3>)|(?:<[^<>/]*?/>))([^<>]*)', self.content, flags=re.S): #for every child
            self.children.append(Element(m[1], pre=m[0], post=m[-1])) #recursively add the child to list
        self.childrendict = {} #we have children (maybe) but we don't know that yet
        for c in self.children: #for every child
            if not c.name in self.childrendict: #if this element hasn't been found yet
                self.childrendict[c.name] = [c] #name = list of elements with that name
            else:
                self.childrendict[c.name].append(c) #add this element to list of elements with its name
    def toString(self):
        """Return a DOM string (minified) of this element."""
        self._updateChildren()
        result = '<' + self.name + ''.join([' ' + k + '="' + v + '"' for k, v in self.attrib.items()]) + '>' #<element attrib1="attribv" attrib2="attribv">
        if self.children: #if this element has children
            for c in self.children: #for every child asdf<elem>...</elem>fdsa
                result += c.pre #asdf
                result += c.toString() #<elem>...</elem>
                result += c.post #fdsa
        else: #no children
            if self.content: #if there aren't any children but we do have content
                result += self.content #content
            else: #no childre, no content
                result = result[:-1] + '/>' #make it <elem/>
                return result #return now
        result += '</' + self.name + '>' #add </element>
        return result #return
    def removechildren(self, f, **kwargs):
        """Recursively remove all of an element e's children
that match the condition f.

f must be a function, with one required argument, into
which will be passed the element being currently worked on.
It must return a boolean.

The original element will have all children removed that made
f return True."""
        for c in self.children: #for every child
            c.removechildren(f, p=self) #remove that child's children too
        p = kwargs.get('p', None) #get this element's parent (None if no parent)
        if p: #if we have a parent
            if f(self): #if the function returns True on ourself
                p.children[p.children.index(self)+1].pre = self.pre + self.post + p.children[p.children.index(self)+1].pre #add our pre and post to the next element
                p.children.pop(p.children.index(self)) #remove ourself
                p._updateChildren() #update parent's children dict
    def returnchildren(self, f, **kwargs):
        """Recursively return all of an element e's children
that match the condition f.

f must be a function, with one required argument, into
which will be passed the element being currently worked on.
It must return a boolean.

The return value is a list of all child elements that made f return
True."""
        result = [] #no matches yet
        for c in self.children: #for every child
            result.extend(c.returnchildren(f, p=self)) #look for the child's children that match
        p = kwargs.get('p', None) #get this element's parent
        if p: #if we have a parent
            if f(self): #if the function returns True on ourself
                result.append(self) #add ourself to the results
        return result #return

def elemdict(text):
    """Make a dictionary of elements instead of an object.

In an element dict, the key @ is its innerHTML, * is
its outerHTML, and ? is its attributes as a dict.

Any other keys are lists of child elements of that name."""
    root = Element(text) #just quickly make an element out of it anyway
    elem = {'?': root.attrib} #store its attributes under the key ?
    for c in root.children: #for every child
        if not c.name in elem: #if the child's name hasn't been recorded yet
            elem[c.name] = [elemdict(c.text)] #recursively add its name and itself
        else: #otherwise
            elem[c.name].append(elemdict(c.text)) #just add the element to its list under its name
    #note: there's no point in having its children as a plain list.
    elem['@'] = root.content #innerHTML
    elem['*'] = root.text #outerHTML
    return elem

def rchildren(elem,indent=0): #recursively print children
    """Recursively print an element's children.

The return value is a string in the format:
base element
|-child element
| |-grandchild element
| |-another grandchild element
| | |-great-grandchild element
|-another child element"""
    result = ('| ' * (indent - 1)) + ('|-' * bool(indent)) + str(elem) #add itself to the string
    for child in elem.children: #and for every one of its children
        result += '\n' + rchildren(child, indent+1) #add it with one more indent
    return result #finally return the string

if __name__ == '__main__': #demo html
    DOM = '''<html>
    <head>
        <title>asdf</title>
        <link rel="stylesheet" href="stylesheet.css"/>
    </head>
    <body>
        <h1>Woo!</h1>
    </body>
</html>''' #demo file
    test = Element(DOM) #make an element out of the DOM
    print('Original DOM:\n' + DOM)
    print('\nRecursively printed objectified DOM:\n' + rchildren(test)) #recursively print its children
    print('\nDictified DOM:\n' + str(elemdict(DOM))) #print the dictionary form
