class PriorityList(object):

    def __init__(self, *args):
        #for each arg (string), read conditionals and determine checks
        for a in args:
            print a #to implement later
        return
    
    def __getattr__(self, name):
        object.__getattribute__(self, name)
