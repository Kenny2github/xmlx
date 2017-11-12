"""
xmlx - a small and compact XML parser in Python.
Example usage:

>>> dom = '''<html>
<head><title>Hi</title></head>
<body>
<h1>Hello</h1>
<p style="color:red">What's up?</p>
<p>Not much.</p>
</body>
</html>'''
>>> html = xmlx.Element(dom)
>>> html
<html>...</html at 0x...>
>>> html.children
[<head>...</head at 0x...>, <body>...</body at 0x...>]
>>> html.returnchildren(lambda e: 'style' in e.attrib)
[<p style="color:red">...</p at 0x...>]
>>> html.returnchildren(lambda e: e.name == 'p')
[<p style="color:red">...</p at 0x...>, <p>...</p at 0x...>]
>>> html.removechildren(lambda e: e.name == 'p')
>>> html.returnchildren(lambda e: e.name == 'p')
[]
>>> dom = html.tostring()
"""
import re #wow this is literally the only module used 0.0

__all__ = ['Element']

class _updatingList(list, object): #updating list
    '''A list that updates the element's text whenever an item is edited or deleted.'''
    def __init__(self, iterable=None, ins=None):
        list.__init__(self, [] if iterable is None else iterable)
        self.ins = ins
    def __setitem__(self, key, val):
        list.__setitem__(self, key, val)
        self.ins.tostring(False)
        self.ins.updatechildrenfromcontent()
    def __delitem__(self, key):
        try:
            self.ins.children[key+1].pre = self.ins.children[key].pre \
                                           + self.ins.children[key].post \
                                           + self.ins.children[key+1].pre
        except IndexError:
            if len(self.ins.children) < 2:
                self.ins.content = self.ins.children[key].pre \
                                   + self.ins.children[key].post
            else:
                self.ins.children[key-1].post += self.ins.children[key].pre \
                                                 + self.ins.children[key].post
        list.__delitem__(self, key)
        self.ins.tostring(False)
        self.ins.updatechildrenfromcontent()
    def __delslice__(self, start, stop):
        for i in range(start, stop):
            self.__delitem__(i)

class Element(object):
    """A Python object representing an XML element."""
    def __str__(self):
        """Return a string representation of the element."""
        return '<' \
               + self.name \
               + ' ' * int(bool(self.attrib)) \
               + ' '.join([k + '="' + v + '"' \
                           for k, v in list(self.attrib.items())[:3]]) \
               + '>...</' + self.name + ' at ' + hex(id(self)) + '>'
    __repr__ = __str__
    def __hash__(self):
        return hash(self.tostring())
    def __eq__(self, other):
        return hash(self) == hash(other)
    def __init__(self, text, **xtrs):
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
format "name":<element>. {"b":<b>...</b>} for this case
'''
        assert isinstance(text, str), \
               "expected str, got " \
               + type(text).__name__
        text = re.sub(r'<[!\?].*?>',
                      '',
                      text,
                      flags=re.S).strip()
        assert bool(re.match(r'((?:<([^<>/]*?)(?: [^<>]*?)?>.*?</\2>)|(?:<[^<>/]*?/>))',
                             text, re.S)), "text does not match element format"
        if re.match(r'<[^<>/]*?/>', text, re.S):
            self.name = re.match('<([^<>/]*?)(?: [^<>]*?)?/>',
                                 text,
                                 re.S).group(1)
            self.attrib = {}

            for match in re.finditer(' (?P<name>[^<>/]*?)=(?:[\'"](?P<valueq>[^<>]*?)[\'"]'
                                     + '|(?P<valuewq>[^<>/\'"]*))',
                                     re.search('<[^<>/]*?((?: [^<>/]*?)*?)?/>',
                                               text,
                                               flags=re.S).group(1),
                                     flags=re.S):
                self.attrib[match.group('name')] = match.group('valueq') \
                                               or match.group('valuewq') \
                                               or ''

            self.content = ''
            self.text = text
            self.pre = xtrs.get('pre', '')
            self.post = xtrs.get('post', '')
            self.updatechildrenfromcontent()
        else:
            self.name = re.match(r'<([^<>/]*?)(?: [^<>]*?)?>.*?</\1>',
                                 text,
                                 re.S).group(1)
            self.attrib = {}

            for match in re.finditer(' (?P<name>[^<>/]*?)=(?:[\'"](?P<valueq>[^<>]*?)[\'"]'
                                     + '|(?P<valuewq>[^<>/\'"]*))',
                                     re.search('<[^<>/]*?((?: [^<>]*?)*?)>',
                                               text,
                                               flags=re.S).group(1),
                                     flags=re.S):
                self.attrib[match.group('name')] = match.group('valueq') \
                                               or match.group('valuewq') \
                                               or ''

            self.content = re.match(r'<([^<>/]*?)(?: [^<>]*?)?>(?P<text>.*?)</\1>',
                                    text,
                                    flags=re.S).group('text')
            self.text = text
            self.pre = xtrs.get('pre', '')
            self.post = xtrs.get('post', '')
            self.updatechildrenfromcontent()
    def updatechildrenfromcontent(self):
        """Update children list from content."""
        self.children = []
        for match in re.findall(r'([^<>]*)((?:<([^<>/]*?)(?: [^<>]*?)?>.*?</\3>)'
                                + '|(?:<[^<>/]*?/>))([^<>]*)',
                                self.content,
                                flags=re.S):
            self.children.append(Element(match[1], pre=match[0], post=match[-1]))

        self.children = _updatingList(self.children, self)
    def tostring(self, fromcontent=True):
        """Return a DOM string (minified) of this element."""
        if fromcontent:
            self.updatechildrenfromcontent()
        result = '<' + self.name \
                 + ''.join([' ' + k + '="' + v + '"'
                            for k, v in self.attrib.items()]) + '>'
        if self.children:
            for child in self.children:
                result += child.pre
                result += child.tostring()
                result += child.post
        else:
            if self.content:
                result += self.content
            else:
                result = result[:-1] + '/>'
                return result
        result += '</' + self.name + '>'
        if fromcontent:
            return result
        else:
            self.text = result
            self.content = re.match(r'<([^<>/]*?)[^<>/]*?>(?P<text>.*?)</\1>',
                                    self.text, flags=re.DOTALL).group('text')
    def removechildren(self, func, **kwargs):
        """Recursively remove all of an element e's children
that match the condition func.

func must be a function, with one required argument, into
which will be passed the element being currently worked on.
It must return a boolean.

The original element will have all children removed that made
func return True.
"""
        for child in self.children:
            print('this', self.name, 'has', len(self.children), 'children')
            print(child.name)
            child.removechildren(func, p=self)
        parent = kwargs.get('p', None)
        if parent:
            if func(self):
                for child in parent.children:
                    print(len(parent.children), 'children')
                    if self == child:
                        print('delete', child.name)
                        del parent.children[parent.children.index(child)]
    def returnchild(self, func):
        """Return the first child that matches the condition func.

func must be a function, with one required argument, into
which will be passed the element being currently worked on.
It must return a boolean.

The return value is either a single element that made func return True,
or None.
"""
        if func(self):
            return self
        else:
            if self.children:
                for child in self.children:
                    has = child.returnchild(func)
                    if has is not None:
                        return has
            else:
                return None
    def returnchildren(self, func):
        """Recursively return all of the element's children
that match the condition func.

func must be a function, with one required argument, into
which will be passed the element being currently worked on.
It must return a boolean.

The return value is a tuple of all child elements that made func return
True.
"""
        result = []
        for child in self.children:
            result.extend(child.returnchildren(func))
        if func(self):
            result.insert(0, self)
        return tuple(result)

    def queryselector(self, selector, **kwds):
        """Return the first child (including self) that matches a CSS
        selector."""
        expression = re.compile(r'(?=[\s\S]+)(?:(?P<name>[-a-zA-Z]+\
[-a-zA-Z0-9]*)?(?:(?P<class>\.[-a-zA-Z]+[-a-z-A-Z0-9]*)|(?P<id>#[-a-zA-Z]*\
[-a-zA-Z0-9]*)){0,2}(?P<attrib>\[(?P<key>[-a-zA-Z]+[-a-zA-Z0-9]*)\
(?:(?P<eqmod>[$|^~*])?=(?P<value>[-a-zA-Z]+[-a-zA-Z0-9]*))?\])?|\*)')
        selec = re.match(expression, selector)
        assert selec
        nam = selec.group('name')
        cls = selec.group('class')
        ids = selec.group('id')
        key = selec.group('key')
        emd = selec.group('eqmod')
        val = selec.group('value')
        exp = 'el.name == '
        exp += 'el.name' if nam in (None, '*') else repr(nam)
        exp += " and el.attrib.get('class', None) == "
        exp += "el.attrib.get('class', None)" if cls is None else repr(cls[1:])
        exp += " and el.attrib.get('id', None) == "
        exp += "el.attrib.get('id', None)" if ids is None else repr(ids[1:])
        exp += " and ("
        if emd == None:
            exp += "el.attrib.get("
            exp += repr(key)
            exp += ", None) == "
            exp += "el.attrib.get(" + repr(key) + ', None)' if val is None \
                   else repr(val)
        elif emd == '$':
            exp += "el.attrib.get("
            exp += repr(key)
            exp += ", '').endswith("
            exp += repr(val)
            exp += ')'
        elif emd == '|':
            exp += "el.attrib.get("
            exp += repr(key)
            exp += ", None) == "
            exp += repr(val)
            exp += " or el.attrib.get("
            exp += repr(key)
            exp += ", '').startswith("
            exp += repr(val)
            exp += " + '-')"
        elif emd == '^':
            exp += "el.attrib.get("
            exp += repr(key)
            exp += ", '').startswith("
            exp += repr(val)
            exp += ')'
        elif emd in ('~', '*'):
            exp += repr(val)
            exp += ' in el.attrib.get('
            exp += repr(key)
            exp += ", '')"
        exp += ')'
        if kwds.get('every', False):
            return self.returnchildren(lambda el: eval(exp))
        return self.returnchild(lambda el: eval(exp))

    def queryselectorall(self, selector):
        """Return a tuple of all children (including self) that match a CSS
        selector."""
        return self.queryselector(selector, every=True)
