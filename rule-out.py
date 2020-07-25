import sys
import string
import re
import ast
from stanza.server import CoreNLPClient
from bllipparser import RerankingParser
from nltk.tree import ParentedTree
from nltk.treeprettyprinter import TreePrettyPrinter
from pattern.en import conjugate
from pattern.en import INFINITIVE, PRESENT, SG, SUBJUNCTIVE, PAST, PARTICIPLE


rrp = RerankingParser.from_unified_model_dir('/home/e/.local/share/bllipparser/WSJ+Gigaword')  
client = CoreNLPClient(annotators=['parse'], timeout=30000, memory='8G')

test1 = "He wouldn't make the rice if it had already been made."
test2 = "The first plumber, who arrived before three, and the second, who arrived after four, both said the pipe was clogged."
test3 = "The doctor who talked to us said the swelling would probably be gone after two days."
tests = {test1, test2, test3}

auxes = {'have', 'be', 'do', 'would', 'could',  'might'}
clause_levels = {'S', 'SBAR', 'SBARQ', 'SINV', 'SQ'}
root_levels = {'ROOT', 'S1'}
punct = {'.', '.', '?'}

def stanford_parse(s):
    ann = client.annotate(s, output_format='json')
    return ann['sentences'][0]['parse']
    
def bllip_parse(s):
    return rrp.simple_parse(s)

# This guards against multiple identical
# subtrees appearing in the full tree barring
# some bizarre literary case like
# "We saw the cars go by and we saw the cars go by"
def peq(p1, p2):
    teq = p1 == p2
    place_eq = p1.parent() == p2.parent()
    return teq and place_eq

def children(ptree):
    return [stree for stree in ptree]

def non_finite(v):
    return {conjugate(v, INFINITIVE),
            conjugate(v, PAST+PARTICIPLE),
            conjugate(v, PRESENT+PARTICIPLE)}

def is_non_finite(v):
    return v in non_finite(v)

def is_aux(v):
    return (v.label() == 'MD') or (conjugate(children(v)[0], INFINITIVE) in auxes) 

def is_non_aux(v):
    return v.label()[:2] == 'VB'

# returns the nearest upper embedded clause
# (determines if the immediate clause is embedded) 
def sup_embedded(ptree):
    if ptree.label() in root_levels.union(clause_levels):
        # this happens often with coordinated conjunctions and does not
        # constitute embedding
        if (ptree.parent().label() in root_levels.union(clause_levels)):
            return None
        else:
            return ptree
    else:
        sup_embedded(ptree.parent()) 

# returns the nearest lower embedded clauses
def inf_embedded(ptree, embedded = []):
    if children(ptree) == ptree.leaves():
        return None
    elif ptree.label() in root_levels:
        for stree in ptree:
            if stree.label() in clause_levels:
                inf_embedded(stree, embedded)
    elif ptree.label() in clause_levels:
        for stree in ptree:
            if stree.label() not in clause_levels:
                inf_embedded(stree, embedded)
    elif ptree.label() not in root_levels.union(clause_levels):
        for stree in ptree:
            if stree.label() in clause_levels:
                embedded.append(stree)
            else:
                inf_embedded(stree, embedded)        
    return embedded

def is_simple(ptree): 
    return all([(not contains_embedded(stree)) for stree in ptree.root()])

def find_childen(ptree, label):
    results = []
    for child in ptree:
        if child.label() == label:
            results.append(child)
    return results

def rule_out(ptree):
    pass

def list2ptree(s):
    return ParentedTree.fromstring(s)

def overt_not_aux(ptree):
    return not is_aux(clause_overt_v_head(ptree)) 

def main():
    for test in tests:
        s_parse_tree = stanford_parse(test)
        s_final = list2ptree(s_parse_tree)
        #b_parse_tree = rrp.simple_parse(test)
        #b_final = list2ptree(b_parse_tree)
        s_final.pretty_print()
        for elem in inf_embedded(s_final):
            elem.pretty_print()
        
if __name__ == "__main__":
    main()

'''
def clause_overt_v_head(ptree):
    head_tag = children(ptree)[0]
    if ptree.label() in root_levels:
        return clause_overt_v_head(head_tag)
    if ptree.label() in clause_levels:
        if head_tag.label() in clause_levels.union('VP'):
            return clause_overt_v_head(head_tag)
    if ptree.label() == 'VP':
        if head_tag.label() == 'VP':
            return clause_overt_v_head(head_tag)
        else:
            return head_tag
'''

    
