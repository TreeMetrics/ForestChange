"""
Core code for adding UsageGroup to argparse.py
This is a generalization of _MutuallyExclusiveGroup
usagegroups may nest (appended to a _group_actions list)
Each group has its own test_function which is run at the end of _parse_known_args.
A group may also have formatting characters or string to be used in the
usage line and error messages.

Sample setups:

parser = argparse.ArgumentParser(prog='PROG',
    formatter_class=argparse.UsageGroupHelpFormatter)

g1 = parser.add_usage_group(dest='FILE or DIR', kind='mxg', required=True)
a_file= g1.add_argument("-o", "--outfile", metavar='FILE')

g2 = g1.add_usage_group(dest='DIR and PS', kind='inc')
a_dir = g2.add_argument("-O", "--outdir", metavar='DIR')

g3 = g2.add_usage_group(dest='P or S', kind='mxg')
a_pat = g3.add_argument("-p", "--outpattern", metavar='PATTERN')
a_suf = g3.add_argument("-s", "--outsuffix", metavar='SUFFIX')
# usage: PROG [-h] (-o FILE | (-O DIR & (-p PATTERN | -s SUFFIX)))

parser = argparse.ArgumentParser(formatter_class=argparse.UsageGroupHelpFormatter)
a1 = parser.add_argument('-a', action='store_true')
b1 = parser.add_argument('-b', action='store_false')

g1 = parser.add_usage_group(kind='not', required=True)
g1.add_usage_group(kind='not').add_argument(a1)
g1.add_usage_group(kind='not', dest='not(b)').add_argument(b1)

g2 = parser.add_usage_group(kind='all', dest='all(a,b)')
g2.add_argument(a1)
g2.add_argument(b1)
# usage: stack22929087.py [-h] not(not(-a), not(-b)) (-a & -b)

Sample usage lines:
usage: stack22929087.py cmd1 [-h] (--wid WID | (--w1 W1 & --w2 W2))
                             [not(-g G) ^ --wid WID]
usage: simple_mxg.py [-h] [--foo FOO] [--bar BAR | --foo FOO]
"""



class UsageGroup(_AttributeHolder, _ArgumentGroup):

    def __init__(self, container, **kwargs):
        # call super with subset of the kwargs
        ag_keys = ['title', 'description', 'prefix_chars',
                    'argument_default', 'conflict_handler']
        args = {k:kwargs[k] for k in ag_keys if k in kwargs}
        super(UsageGroup, self).__init__(container, **args)
        self.container = container  # _container to be consistent with MXG
        self.dest = kwargs.pop('dest', '')
        self.required = kwargs.pop('required', False)
        self.parens = kwargs.pop('parens', None)
        self.joiner = kwargs.pop('joiner', None)
        self.testfn = kwargs.pop('testfn', None)
        self.usage = kwargs.pop('usage', None)
        self.kind = kwargs.pop('kind', None)
        if isinstance(container, ArgumentParser):
            self.parser = container # place to put Actions
        else:
            self.parser = getattr(container, 'parser', container)

        self.register_test()
        # potentially might define Action like attributes to help format it
        # e.g. help, option_strings
        for k in ag_keys: kwargs.pop(k, None)
        if len(kwargs.keys()):
            print('left over kwargs:', kwargs)
            # do we object to these (view them as errors)
            # or ignore them
            # or add them to the object (to be used, for example, in the test)?

    def _get_kwargs(self):
        names = [
            'dest',
            'usage',
            'kind',
            'required',
            'testdoc',
        ]
        return [(name, getattr(self, name)) for name in names]

    def register_test(self):
        # define formatting and testing, based on 'kind' and 'required'
        # (and potentially other attributes)
        # some alternatives only differ in the choice of 'joiner'
        # '1st' level tests are registered with parser
        # nested tests are executed recursively
        name = str(id(self)) # a unique key for this test
        if self.kind in ['mxg', 'mx', 'ecl', 'excl', 'exclusive']:
            joiner, parens, testfn = self.test_mx_group()
        elif self.kind in ['xor']:
            joiner, parens, testfn = self.test_mx_group()
            joiner = ' ^ '
            # ^ is the bitwise xor; but | is the legacy mxg joiner
        elif self.kind in ['inc', 'inclusive', 'all']:
            joiner, parens, testfn = self.test_inc_group()
        elif self.kind in ['or']:
            joiner, parens, testfn = self.test_any_group()
        elif self.kind in ['any']:
            joiner, parens, testfn = self.test_any_group()
            joiner = ' , '
        elif self.kind in ['not']:
            joiner, parens, testfn = self.test_not_group()
        else:
            joiner, parens, testfn = self.test_not_group()
        if self.joiner is None: self.joiner = joiner
        if self.parens is None: self.parens = parens
        if self.testfn is None: self.testfn = testfn
        self.testdoc = testfn.__doc__
        if isinstance(self.container, UsageGroup):
            pass
        else:
            # register testfn with common register (container)
            self.container.register('usage_tests', name, self.testfn)

    def _format_args(self, *args):
        return ''

    def _add_action(self, action):
        if self.kind in ['mxg'] and action.required:
            msg = _('mutually exclusive arguments must be optional')
            raise ValueError(msg)
        # add action to parser, but not container
        action = self.parser._add_action(action)
        self._group_actions.append(action)
        return action

    def add_usage_group(self, *args, **kwargs):
        if len(args) and isinstance(args[0], UsageGroup):
            group = args[0]
            self._group_actions.append(group)
            return group
        # add to own list, not the parsers
        kwargs.pop('title', None) # ignore at this level
        # or give warning about ignored title?
        group = UsageGroup(self, *args, **kwargs)
        self._group_actions.append(group)
        return group

    def add_argument(self, *args, **kwargs):
        # add extension that allows adding a prexisting Action
        if len(args) and isinstance(args[0], Action):
            # add the action to self, but not to the parser (it is already there)
            action =  args[0]
            self._group_actions.append(action)
            return action
        else:
            return super(UsageGroup, self).add_argument(*args, **kwargs)

    def raise_error(self, parser, msg):
        # common method of testfn
        names = [action.dest for action in self._group_actions]
        names = ', '.join(names)
        msg = msg % names
        if self.dest:
            msg = '%s: %s'%(self.dest, msg)
        parser.error(msg)

    def count_actions(self, parser, seen_actions, *vargs, **kwargs):
        # utility that is useful in most kinds of tests
        # count the number of group actions (and groups) that are seen
        seen_actions = set(seen_actions)
        group_actions = self._group_actions
        actions = [a for a in group_actions if isinstance(a, Action)]
        okactions = {a for a in actions if a in seen_actions}
        groups = [a for a in group_actions if isinstance(a, UsageGroup)]
        okgroups = {a for a in groups if a.testfn(parser, seen_actions, *vargs, **kwargs)}
        okactions = okactions.union(okgroups)
        cnt = len(okactions)
        return cnt

    def test_this_group(self):
        def testfn(parser, seen_actions, *vargs, **kwargs):
            # default usage test
            group_actions = self._group_actions
            group_seen = set(seen_actions).intersection(group_actions)
            cnt = len(group_seen)
            print('nested testing',[a.dest for a in group_actions])
        return ', ', '()', testfn

    def test_mx_group(self):
        joiner = ' | ' # something better for xor?
        parens = '()' if self.required else '[]'
        # test equivalent the mutually_exclusive_groups
        def testfn(parser, seen_actions, *vargs, **kwargs):
            "xor()"
            cnt = self.count_actions(parser, seen_actions, *vargs, **kwargs)
            if cnt > 1:
                msg = 'only one the arguments [%s] is allowed'
            elif cnt == 0 and self.required:
                msg = 'one of the arguments [%s] is required'
            else:
                msg = None
            if msg:
                self.raise_error(parser, msg)
            return cnt>0 # True if something present, False if none
        return joiner, parens, testfn

    def test_inc_group(self):
        def testfn(parser, seen_actions, *vargs, **kwargs):
            "all()"
            cnt = self.count_actions(parser, seen_actions, *vargs, **kwargs)

            if cnt == 0 and self.required:
                msg = 'all of the arguments [%s] is required'
            elif 0 < cnt < len(self._group_actions): # all
                    msg = 'all of the arguments [%s] are required'
            else:
                msg = None
            if msg:
                self.raise_error(parser, msg)
            print('inc testing',cnt, [a.dest for a in self._group_actions])
            return cnt>0
        return ' & ', '()', testfn

    def test_any_group(self):
        def testfn(parser, seen_actions, *vargs, **kwargs):
            "any()"
            cnt = self.count_actions(parser, seen_actions, *vargs, **kwargs)
            if cnt == 0 and self.required:
                msg = 'some of the arguments [%s] is required'
            else:
                msg = None
            if msg:
                self.raise_error(parser, msg)
            print('any testing',[a.dest for a in self._group_actions])
            return cnt>0
        return ' | ', '{}', testfn

    def test_not_group(self):
        joiner = ', '
        parens = ['not(',')']
        def testfn(parser, seen_actions, *vargs, **kwargs):
            "not()"
            cnt = self.count_actions(parser, seen_actions, *vargs, **kwargs)
            print('not test', cnt, [a.dest for a in self._group_actions])
            if cnt > 0 and self.required:
                msg = 'none of the arguments [%s] is allowed'
            else:
                msg = None
            if msg:
                self.raise_error(parser, msg)
            return cnt==0
        return joiner, parens, testfn

# adapted from multigroup, issue 10984
class UsageGroupHelpFormatter(HelpFormatter):
    """Help message formatter that handles overlapping mutually exclusive
    groups.

    Only the name of this class is considered a public API. All the methods
    provided by the class are considered an implementation detail.

    This formats all the groups, even if they share actions, or the actions
    do not occur in the other in which they were defined (in parse._actions)
    Thus an action may appear in more than one group
    Groups are presented in an order that preserves the order of positionals
    """

    def _format_usage(self, usage, actions, groups, prefix):
        #
        if prefix is None:
            prefix = _('usage: ')

        # if usage is specified, use that
        if usage is not None:
            usage = usage % dict(prog=self._prog)

        # if no optionals or positionals are available, usage is just prog
        elif usage is None and not actions:
            usage = '%(prog)s' % dict(prog=self._prog)

        # if optionals and positionals are available, calculate usage
        elif usage is None:
            prog = '%(prog)s' % dict(prog=self._prog)
            #optionals = [action for action in actions if action.option_strings]
            #positionals = [action for action in actions if not action.option_strings]

            # build full usage string
            format = self._format_actions_usage
            # (opt_parts, pos_parts) = format(optionals + positionals, groups)
            (opt_parts, arg_parts, pos_parts) = format(actions, groups)
            all_parts = opt_parts + arg_parts + pos_parts

            usage = ' '.join([prog]+all_parts)
            opt_parts = opt_parts + arg_parts # for now join these

            # the rest is the same as in the parent formatter
            # wrap the usage parts if it's too long
            text_width = self._width - self._current_indent
            if len(prefix) + len(usage) > text_width:
                # helper for wrapping lines
                def get_lines(parts, indent, prefix=None):
                    lines = []
                    line = []
                    if prefix is not None:
                        line_len = len(prefix) - 1
                    else:
                        line_len = len(indent) - 1
                    for part in parts:
                        if line and line_len + 1 + len(part) > text_width:
                            lines.append(indent + ' '.join(line))
                            line = []
                            line_len = len(indent) - 1
                        line.append(part)
                        line_len += len(part) + 1
                    if line:
                        lines.append(indent + ' '.join(line))
                    if prefix is not None:
                        lines[0] = lines[0][len(indent):]
                    return lines

                # if prog is short, follow it with optionals or positionals
                if len(prefix) + len(prog) <= 0.75 * text_width:
                    indent = ' ' * (len(prefix) + len(prog) + 1)
                    if opt_parts:
                        lines = get_lines([prog] + opt_parts, indent, prefix)
                        lines.extend(get_lines(pos_parts, indent))
                    elif pos_parts:
                        lines = get_lines([prog] + pos_parts, indent, prefix)
                    else:
                        lines = [prog]

                # if prog is long, put it on its own line
                else:
                    indent = ' ' * len(prefix)
                    parts = opt_parts + pos_parts
                    lines = get_lines(parts, indent)
                    if len(lines) > 1:
                        lines = []
                        lines.extend(get_lines(opt_parts, indent))
                        lines.extend(get_lines(pos_parts, indent))
                    lines = [prog] + lines

                # join lines into usage
                usage = '\n'.join(lines)

        # prefix with 'usage:'
        return '%s%s\n\n' % (prefix, usage)

    def _format_actions_usage(self, actions, groups):
        # usage will list
        # optionals that are not in a group
        # actions in groups, with possible repetitions
        # positionals that not in a group
        # It orders groups with positionals to preserved the parsing order
        actions = actions[:] # work with copy, not original
        groups = self._group_sort(actions, groups)
        seen_actions = set()
        arg_parts = []
        for group in groups:
            #gactions = group._group_actions
            if True:
                group_parts, gactions = self._format_group_usage(group)
                seen_actions.update(gactions)
                arg_parts.extend(group_parts)

        # now format all remaining actions
        for act in seen_actions:
            try:
                actions.remove(act)
            except ValueError:
                pass
        # find optionals and positionals in the remaining actions list
        # i.e. ones that are not in any group
        optionals = [action for action in actions if action.option_strings]
        positionals = [action for action in actions if not action.option_strings]

        opt_parts = self._format_just_actions_usage(optionals)
        #arg_parts = parts + arg_parts

        pos_parts = self._format_just_actions_usage(positionals)
        # keep pos_parts separate, so they can be handled separately in long lines
        return (opt_parts, arg_parts, pos_parts)

    def _group_sort(self, actions, groups):
        # sort groups by order of positionals, if any
        from operator import itemgetter
        if len(groups)==0:
            return groups
        optionals = [action for action in actions if action.option_strings]
        positionals = [action for action in actions if not action.option_strings]

        # create a sort key, based on position of action in actions
        posdex = [-1]*len(groups)
        noInGroups = set(positionals)
        for i,group in enumerate(groups):
            for action in group._group_actions:
                if action in positionals:
                    posdex[i] = positionals.index(action)
                    noInGroups.discard(action)
        sortGroups = groups[:]
        # actions not found in any group are put in their own tempory groups
        samplegroup = group
        for action in noInGroups:
            g = _copy.copy(samplegroup)
            g.required = action.required
            g._group_actions = [action]
            sortGroups.append(g)
            posdex.append(positionals.index(action))

        sortGroups = sorted(zip(sortGroups,posdex), key=itemgetter(1))
        sortGroups = [i[0] for i in sortGroups]
        return sortGroups

    def _format_group_usage(self, group):
        # format one group
        joiner = getattr(group, 'joiner', ' | ')
        parens = '()' if group.required else '[]'
        parens = getattr(group, 'parens', parens) # let group define its own brackets
        usage = getattr(group, 'usage', None)
        if usage:
            # shortcut if usage is given
            # what actions, if any, should be returned
            # safe to assume usage is a string, as opposed to list?
            return [usage], {}
        seen_actions = set()
        actions = group._group_actions
        parts = []

        parts += parens[0]
        for action in actions:
            if isinstance(action, UsageGroup):
                part, gactions = self._format_group_usage(action)
                seen_actions.update(gactions)
                part = part[0]
            else:
                part = self._format_just_actions_usage([action])
                part = _re.sub(r'^\[(.*)\]$', r'\1', part[0]) # remove 'optional'[]
                seen_actions.add(action)
            if part:
                parts.append(part)
                parts.append(joiner)
        if len(parts)>1:
            parts[-1] = parens[1]
        else:
            # nothing added
            parts = []
        arg_parts = [''.join(parts)]

        def cleanup(text):
            # remove unnecessary ()
            pat = r'^\(([^(%s)]*)\)$'%joiner # is this robust enough?
            text = _re.sub(pat, r'\1', text)
            return text
        # this cleanup applies if group is empty or has single item
        # lets skip this for now
        # arg_parts = [cleanup(t) for t in arg_parts]
        return arg_parts, seen_actions

# methods to add to _ActionsContainer

    def add_mutually_exclusive_group(self, **kwargs):
        # can replace Mutually_Exclusive_Group with a UsageGroup
        kwargs.update(kind='mxg')
        return self.add_usage_group(**kwargs)

    def add_usage_group(self, **kwargs):
        # create a UsageGroup and add it self
        # if a title is given, first create an ArgumentGroup
        if 'title' in kwargs:
            ag_keys = ['title', 'description', 'prefix_chars',
                       'argument_default', 'conflict_handler']
            args = {k:kwargs[k] for k in ag_keys if k in kwargs}
            container = self.add_argument_group(**args)
        else:
            container = self
        #kwargs.pop('title', None)
        #kwargs.pop('description', None)
        group = UsageGroup(container, **kwargs)
        container._mutually_exclusive_groups.append(group)
        return group