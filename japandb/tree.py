import os

CONST_SEARCH_SENTENCE_LIMIT = 20

class Nd:
    cts = None # contents
    cld = None # children
    ar = None # article/sentence_num pair
    
    def __init__(self, cts, cld, ar=None):
        self.cts = cts
        self.cld = cld
        self.ar = ar

class GST: # Generalized Suffix Tree
    root = None
    
    def __init__(self):
        self.root = Nd('', [])
        
    def add(self, word, article_info):
        for i in range(len(word)):  
            curr_node = self.root
            subword = word[i:len(word)]
            while True:
                prefix = len(os.path.commonprefix([subword, curr_node.cts]))
                if prefix > 0:
                    if prefix < len(curr_node.cts):
                        # first add a child for the non-shared part of curr_node
                        curr_node_suffix = Nd(curr_node.cts[prefix:], curr_node.cld, curr_node.ar)
                        # turn curr_node into a parent
                        curr_node.cld = [curr_node_suffix]
                        curr_node.ar = None
                        # shrink text in curr_node
                        curr_node.cts = curr_node.cts[:prefix]
                        # removed shared content from subword
                        subword = subword[prefix:]
                        curr_node = GST.get_branch(curr_node, subword, article_info)
                        if curr_node is None:
                            break
                    else:
                        # check if the curr_node is a leaf
                        if curr_node.ar is not None:
                            old_end = Nd('', [], curr_node.ar)
                            new_end = Nd(subword[prefix:], [], article_info)
                            curr_node.ar = None
                            curr_node.cld = [old_end, new_end]
                            break
                        else:
                            subword = subword[prefix:]
                            curr_node = GST.get_branch(curr_node, subword, article_info)
                            if curr_node is None:
                                break
                else:
                    # note: only way nothing can be shared at all is if we compared root
                    curr_node = GST.get_branch(curr_node, subword, article_info)
                    if curr_node is None:
                        break
    
    @staticmethod
    def get_branch(curr_node, subword, article_info):
        if len(subword) > 0:
            for child in curr_node.cld:
                if(child.cts[:1] == subword[:1]):
                    return child
                    
        new_node = Nd(subword, [], article_info)
        curr_node.cld.append(new_node)
        return None
    
    @staticmethod
    def recursive_print(node):
        if len(node.cld) > 0:
            result = node.cts + ' ( '
            for i in range(len(node.cld)):
                result += GST.recursive_print(node.cld[i])
                if i != len(node.cld) - 1:
                    result += ', '
            
            return result + ' )'
        else:
            if node.ar is not None:
                result = '^'+str(node.ar)+'^'
            else:
                result = '^None^'
            return node.cts+result
    
    @staticmethod
    def bfs(nodes, articles):
        if len(nodes) == 0 or len(articles) > CONST_SEARCH_SENTENCE_LIMIT:
            return articles
            
        next_depth = []
        for child in nodes:
            if child.ar is not None:
                articles.append(child.ar)
            else:
                next_depth.extend(child.cld)
                
        return GST.bfs(next_depth, articles)
    
    def find(self, word):
        curr_node = self.root
        while True:
            prefix = len(os.path.commonprefix([word, curr_node.cts]))
            if prefix == len(word):
                if curr_node.ar is not None:
                    return [curr_node.ar]
                else:
                    return GST.bfs(curr_node.cld, [])
            if prefix > 0:
                word = word[prefix:]
            
            # word contains more than curr_node
            for child in curr_node.cld:
                if child.cts[:1] == word[:1]:
                    curr_node = child
                    break
            else:
                return None # no cld continue in same way search does
    
    def __str__(self):
        return GST.recursive_print(self.root)
    
    