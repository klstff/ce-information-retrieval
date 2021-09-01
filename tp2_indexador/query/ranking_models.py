from typing import List
from abc import abstractmethod
from typing import List, Set, Mapping
from index.structure import TermOccurrence
import math
from enum import Enum

class IndexPreComputedVals():
    def __init__(self,index):
        self.index = index
        self.precompute_vals()

    def precompute_vals(self):
        """
            Inicializa os atributos por meio do indice (idx):
            doc_count: o numero de documentos que o indice possui
            document_norm: A norma por documento (cada termo é presentado pelo seu peso (tfxidf))
        """
        
        self.document_norm, self.idf, doc_weight = {}, {}, {}
        self.doc_count = self.index.document_count
        
        if not self.doc_count: self.doc_count = self.index.document_count
        for term, term_file_position in self.index.dic_index.items():
            for occurrence in self.index.get_occurrence_list(term):
                weight = VectorRankingModel.tf_idf(self.doc_count, occurrence.term_freq, term_file_position.doc_count_with_term) ** 2
                self.idf[term] = VectorRankingModel.idf(self.doc_count, term_file_position.doc_count_with_term)
                doc_weight[occurrence.doc_id] = doc_weight[occurrence.doc_id] + weight if occurrence.doc_id in doc_weight else weight
                    
        for doc_id, doc in doc_weight.items():
            self.document_norm[doc_id] = math.sqrt(doc)

        
class RankingModel():
    @abstractmethod
    def get_ordered_docs(self,query:Mapping[str,TermOccurrence],
                              docs_occur_per_term:Mapping[str,List[TermOccurrence]]) -> (List[int], Mapping[int,float]):
        raise NotImplementedError("Voce deve criar uma subclasse e a mesma deve sobrepor este método")

    def rank_document_ids(self,documents_weight):
        doc_ids = list(documents_weight.keys())
        doc_ids.sort(key= lambda x:-documents_weight[x])
        return doc_ids

class OPERATOR(Enum):
  AND = 1
  OR = 2
    
#Atividade 1
class BooleanRankingModel(RankingModel):
    def __init__(self,operator:OPERATOR):
        self.operator = operator

    def intersection_all(self,map_lst_occurrences:Mapping[str,List[TermOccurrence]]) -> List[int]:
        set_ids = set()
        set_discover_ids = set()
        for lst_occurrences in map_lst_occurrences.values():
            for occurrence in lst_occurrences:
                set_ids.add(occurrence.doc_id) if occurrence.doc_id in set_discover_ids else set_discover_ids.add(occurrence.doc_id)
        return list(set_ids)
    
    def union_all(self,map_lst_occurrences:Mapping[str,List[TermOccurrence]]) -> List[int]:
        set_ids = set()
        for lst_occurrences in map_lst_occurrences.values():
            for occurrence in lst_occurrences:
                if occurrence.doc_id not in set_ids: set_ids.add(occurrence.doc_id)
        return list(set_ids)
    
    def get_ordered_docs(self,query:Mapping[str,TermOccurrence], map_lst_occurrences:Mapping[str,List[TermOccurrence]]) -> (List[int], Mapping[int,float]):
        """Considere que map_lst_occurrences possui as ocorrencias apenas dos termos que existem na consulta"""
        if self.operator == OPERATOR.AND:
            return self.intersection_all(map_lst_occurrences),None
        else:
            return self.union_all(map_lst_occurrences),None

#Atividade 2
class VectorRankingModel(RankingModel):
    def __init__(self,idx_pre_comp_vals:IndexPreComputedVals):
        self.idx_pre_comp_vals = idx_pre_comp_vals

    @staticmethod
    def tf(freq_term:int) -> float:
        TF = 1 + math.log(freq_term, 2) if freq_term != 0 else 0
        return TF

    @staticmethod
    def idf(doc_count:int, num_docs_with_term:int)->float:
        IDF = math.log(doc_count/num_docs_with_term, 2)
        return IDF

    @staticmethod
    def tf_idf(doc_count:int, freq_term:int, num_docs_with_term) -> float:
        tf = VectorRankingModel.tf(freq_term)
        idf = VectorRankingModel.idf(doc_count, num_docs_with_term)
        return tf*idf

    def get_ordered_docs(self,query:Mapping[str,TermOccurrence], docs_occur_per_term:Mapping[str,List[TermOccurrence]]) -> (List[int], Mapping[int,float]):
            documents_weight, idf, doc_weight = {}, {}, {}
            doc_lst = []
            doc_count = 0 
            
            for item in docs_occur_per_term:
                for occurrence in docs_occur_per_term[item]:
                    if occurrence.doc_id not in doc_lst: doc_lst.append(occurrence.doc_id)
                    if occurrence.doc_id > doc_count: doc_count = occurrence.doc_id
                        
            for term in docs_occur_per_term.keys():
                num_docs_with_term = len(docs_occur_per_term[term])
                for item in docs_occur_per_term[term]:
                    w_iq = VectorRankingModel.tf_idf(doc_count, query[term].term_freq, num_docs_with_term)
                    w_ij = VectorRankingModel.tf_idf(self.idx_pre_comp_vals.doc_count,item.term_freq, num_docs_with_term)
                    if term not in idf: idf[term] = []
                    idf[term].append((item.doc_id, w_ij*w_iq))
                    
            for term in idf:
                for occurrence in idf[term]:
                    doc_weight[occurrence[0]] = doc_weight[occurrence[0]] + occurrence[1] if occurrence[0] in doc_weight else occurrence[1]
                        
            for doc_id in doc_lst:
                documents_weight[doc_id] = doc_weight[doc_id]/self.idx_pre_comp_vals.document_norm[doc_id]
        
            #retona a lista de doc ids ordenados de acordo com o TF IDF
            return self.rank_document_ids(documents_weight), documents_weight

