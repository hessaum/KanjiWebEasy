import os

CONST_SEARCH_SENTENCE_LIMIT = 20

class TreeNode:
    contents = None
    children = None
    article = None
    
    def __init__(self, contents, children, article=None):
        self.contents = contents
        self.children = children
        self.article = article

class GeneralizedSuffixTree:
    root = None
    
    def __init__(self):
        self.root = TreeNode('', [])
        
    def add(self, word, article_info):
        for i in range(len(word)):  
            curr_node = self.root
            subword = word[i:len(word)]
            while True:
                prefix = len(os.path.commonprefix([subword, curr_node.contents]))
                if prefix > 0:
                    if prefix < len(curr_node.contents):
                        # first add a child for the non-shared part of curr_node
                        curr_node_suffix = TreeNode(curr_node.contents[prefix:], curr_node.children, curr_node.article)
                        # turn curr_node into a parent
                        curr_node.children = [curr_node_suffix]
                        curr_node.article = None
                        # shrink text in curr_node
                        curr_node.contents = curr_node.contents[:prefix]
                        # removed shared content from subword
                        subword = subword[prefix:]
                        curr_node = GeneralizedSuffixTree.get_branch(curr_node, subword, article_info)
                        if curr_node is None:
                            break
                    else:
                        # check if the curr_node is a leaf
                        if curr_node.article is not None:
                            old_end = TreeNode('', [], curr_node.article)
                            new_end = TreeNode(subword[prefix:], [], article_info)
                            curr_node.article = None
                            curr_node.children = [old_end, new_end]
                            break
                        else:
                            subword = subword[prefix:]
                            curr_node = GeneralizedSuffixTree.get_branch(curr_node, subword, article_info)
                            if curr_node is None:
                                break
                else:
                    # note: only way nothing can be shared at all is if we compared root
                    curr_node = GeneralizedSuffixTree.get_branch(curr_node, subword, article_info)
                    if curr_node is None:
                        break
    
    @staticmethod
    def get_branch(curr_node, subword, article_info):
        if len(subword) > 0:
            for child in curr_node.children:
                if(child.contents[:1] == subword[:1]):
                    return child
                    
        new_node = TreeNode(subword, [], article_info)
        curr_node.children.append(new_node)
        return None
    
    @staticmethod
    def recursive_print(node):
        if len(node.children) > 0:
            result = node.contents + ' ( '
            for i in range(len(node.children)):
                result += GeneralizedSuffixTree.recursive_print(node.children[i])
                if i != len(node.children) - 1:
                    result += ', '
            
            return result + ' )'
        else:
            if node.article is not None:
                result = '^'+str(node.article)+'^'
            else:
                result = '^None^'
            return node.contents+result
    
    @staticmethod
    def bfs(nodes, articles):
        if len(nodes) == 0 or len(articles) > CONST_SEARCH_SENTENCE_LIMIT:
            return articles
            
        next_depth = []
        for child in nodes:
            if child.article is not None:
                articles.append(child.article)
            else:
                next_depth.extend(child.children)
                
        return GeneralizedSuffixTree.bfs(next_depth, articles)
    
    def find(self, word):
        curr_node = self.root
        while True:
            prefix = len(os.path.commonprefix([word, curr_node.contents]))
            if prefix == len(word):
                if curr_node.article is not None:
                    return [curr_node.article]
                else:
                    return GeneralizedSuffixTree.bfs(curr_node.children, [])
            if prefix > 0:
                word = word[prefix:]
            
            # word contains more than curr_node
            for child in curr_node.children:
                if child.contents[:1] == word[:1]:
                    curr_node = child
                    break
            else:
                return None # no children continue in same way search does
    
    def __str__(self):
        return GeneralizedSuffixTree.recursive_print(self.root)
    
    