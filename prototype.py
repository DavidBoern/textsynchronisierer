from __future__ import annotations

# built-in
from collections import defaultdict
from itertools import zip_longest
from typing import Any, Sequence, TypeVar

# app
#from .base import Base as _Base, BaseSimilarity as _BaseSimilarity
#from .types import SimFunc, TestFunc

import itertools

try:
    # external
    import numpy
except ImportError:
    numpy = None  # type: ignore[assignment]


__all__ = [
    'Hamming', 'MLIPNS',
    'Levenshtein', 'DamerauLevenshtein',
    'Jaro', 'JaroWinkler', 'StrCmp95',
    'NeedlemanWunsch', 'Gotoh', 'SmithWaterman',

    'hamming', 'mlipns',
    'levenshtein', 'damerau_levenshtein',
    'jaro', 'jaro_winkler', 'strcmp95',
    'needleman_wunsch', 'gotoh', 'smith_waterman',
]
T = TypeVar('T')

#Klasse Levenshtein erbte ursprünglich von "__Base", diese Funktionalität ist jetzt in Klasse Levenshtein integriert
class Levenshtein():

#ursprünglich aus Base geerbt:
    @staticmethod
    def _ident(*elements: object) -> bool:
        """Return True if all sequences are equal.
        """
        try:
            # for hashable elements
            return len(set(elements)) == 1
        except TypeError:
            # for unhashable elements
            for e1, e2 in zip(elements, elements[1:]):
                if e1 != e2:
                    return False
            return True
  
    def __init__(
        self,
        qval: int = 1,
        test_func: TestFunc | None = None,
        #external: bool = True,
    ) -> None:
        self.qval = qval
        self.test_func = test_func or self._ident
        #self.external = external


    def _cycled(self, s1: Sequence[T], s2: Sequence[T]) -> int:
        rows = len(s1) + 1
        cols = len(s2) + 1
        prev = None
        cur = range(cols)
      
        for r in range(1, rows):
            prev, cur = cur, [r] + [0] * (cols - 1)
            for c in range(1, cols):
                deletion = prev[c] + 1
                insertion = cur[c - 1] + 1
                dist = self.test_func(s1[r - 1], s2[c - 1])
                edit = prev[c - 1] + (not dist)
                cur[c] = min(edit, deletion, insertion)
        return int(cur[-1])

    def __call__(self, s1: Sequence[T], s2: Sequence[T]) -> int:
        s1, s2 = self._get_sequences(s1, s2)
        return self._cycled(s1, s2)
    
    
    def berechneTransformationsmatrix (self, s1: Sequence[T], s2: Sequence[T]) -> int:

        rows = len([c for c in s1 if c != "|"]) + 1 # List comprehension
        cols = len(s2) + 1 
        prev = None
        cur = range(cols)
        transformationsprotokoll = [[None for _ in range(cols)] for _ in range(rows)]
        transformationsprotokoll [0][0] = "0"
        i = 1
        j = 1
        while i<cols:
            transformationsprotokoll [0][i] = "i"
            i=i+1
        while j<rows:
            transformationsprotokoll [j][0] = "d"
            j=j+1 
        r_matrix = 1
        for r_sequenz in range(len(s1)):
            if s1[r_sequenz] == "|": 
                continue          
            prev, cur = cur, [r_matrix] + [0] * (cols - 1)
            for c in range(1, cols):              
                deletion = prev[c] + 1
                insertion = cur[c - 1] + 1
                dist = self.test_func(s1[r_sequenz], s2[c - 1])
                edit = prev[c - 1] + (not dist)
                cur[c] = min(edit, deletion, insertion)
                if cur[c] == edit:
                    transformationsprotokoll[r_matrix][c] = "e"
                elif cur[c] == deletion:
                    transformationsprotokoll[r_matrix][c] = "d"
                else:
                    transformationsprotokoll[r_matrix][c] = "i"
            r_matrix +=1
        for zeile in transformationsprotokoll:   # nur zum Test
            print (zeile)  # nur zum Test
        return transformationsprotokoll
# hier nicht notwendig        return int(cur[-1])

    def __call__(self, s1: Sequence[T], s2: Sequence[T]) -> int:
        s1, s2 = self._get_sequences(s1, s2)
        return self._cycled(s1, s2)

class Tokenuebertragung:
    def uebertrageToken(self, s1: Sequence[T], s2: Sequence[T], transformationsprotokoll: list[list[str]]):
        r_matrix = len (transformationsprotokoll)
        r_sequenz = len(s1)
        i = 0  # ab hier nochmal Indexpositionen checken
        j = 0      
        match transformationsprotokoll[i][j]:
            case "e":
                s1[i] = s2[j]
            case "d":
                s1.pop(i)



        rows = len([c for c in s1 if c != "|"]) + 1
        cols = len(s2) + 1

        return s1_corrected


    
class Kostenfunktion():
    def __init__(self):
        self.aehnlichkeitsmass = {}

    def normiereKostenFunktion(self, dict_Werte):
        faktor = len(dict_Werte)/sum(dict_Werte.values())
        for key in dict_Werte:
            dict_Werte[key]=dict_Werte[key]*faktor
        return dict_Werte       
    
    def erstelleTokenpaare(self, token_List1, token_List2):
        eindeutigeToken = sorted(set(token_List1 + token_List2))
        tokenKombinationen = itertools.combinations(eindeutigeToken,2)
        return tokenKombinationen                              
                
      
    def berechneTokenDistanzen(self, token_List1, token_List2):
        levenshtein = Levenshtein()
        tokenKombinationen = self.erstelleTokenpaare(token_List1,token_List2)
        for tupel in tokenKombinationen:
            self.aehnlichkeitsmass.update({tupel:(levenshtein._cycled(tupel[0], tupel[1]))/(max(len(tupel[0]),len(tupel[1])))})        
        #self.aehnlichkeitsmass = self.normiereKostenFunktion(self.aehnlichkeitsmass)
        print (dict(sorted(self.aehnlichkeitsmass.items(), key=lambda item: item[1])))
        print (self.aehnlichkeitsmass)
        return self.aehnlichkeitsmass
         
            
# k = Kostenfunktion()
# tokenliste1 = ["danke", "volker", "dazu", "gekommen", "bist", "nachdem", "mehrere", "anläufe", "gemacht", "haben", "es", "geht", "um", "die", "70er", "und", "80er", "jahre", "in", "münster", "und", "die", "auseinandersetzung", "um", "die", "frauenstraße", "und", "das", "studentische", "leben, ", "die", "auseinandersetzungen", "an", "der", "uni", "und", "die", "wirkung", "in", "die", "stadt", "hinein", "aber", "zunächst", "möchte", "ich", "deine", "ganz", "persönliche", "geschichte", "hören", "wie", "und", "wo", "bist", "du", "aufgewachsen, ", "wie", "bist", "du", "nach", "münster", "gekommen", "wie", "ging", "es", "im", "studium", "weiter", "und", "wie", "bist", "du", "in", "kontakt", "mit", "der", "frauenstraße"]
# tokenliste2 = ["danke", "volker", "dass", "du", "gekommen", "bist, ", "nachdem", "wir", "ja", "mehrere", "anläufe", "gemacht", "haben", "es", "geht", "um", "die", "70er", "80er", "jahre", "in", "münster", "um", "die", "auseinandersetzung", "um", "die", "frauenstraße", "um", "das", "studentische", "leben", "an", "der", "uni, ", "aber", "auch", "die", "auseinandersetzungen", "dort", "und", "was", "im", "grunde", "genommen", "in", "die", "stadt", "hinein", "wirkte", "aber", "zunächst", "möchte", "ich", "deine", "ganz", "persönliche", "geschichte", "hören", "wie", "und", "wo", "bist", "du", "aufgewachsen", "wie", "bist", "du", "nach", "münster", "gekommen", "ja", "und", "dann", "im", "grunde", "genommen", "wie", "ging", "es", "dann", "im", "studium", "weiter", "und", "wie", "bist", "du", "dann", "auch", "in", "kontakt", "mit", "der", "frauenstraße"]
# individuelleErsetzungskosten = k.berechneTokenDistanzen(tokenliste1, tokenliste2)


b = Levenshtein ()
#tokenliste1 = "Fahr|ra|d"
#tokenliste2 = "Laufrad" 
tokenliste1 = ["danke", "volker", "dazu", "gekommen", "bist", "nachdem", "mehrere", "anläufe", "gemacht", "haben", "es", "geht", "um", "die", "70er", "und", "80er", "jahre", "in", "münster", "und", "die"]
tokenliste2 = ["danke", "volker", "dass", "du", "gekommen", "bist, ", "nachdem", "wir", "ja", "mehrere", "anläufe", "gemacht", "haben", "es", "geht", "um", "die", "70er", "80er", "jahre", "in", "münster", "um", "die"]
#tokenliste1 = ["danke", "volker", "dazu", "gekommen", "bist", "nachdem", "mehrere", "anläufe", "gemacht", "haben", "es", "geht", "um", "die", "70er", "und", "80er", "jahre", "in", "münster", "und", "die", "auseinandersetzung", "um", "die", "frauenstraße", "und", "das", "studentische", "leben, ", "die", "auseinandersetzungen", "an", "der", "uni", "und", "die", "wirkung", "in", "die", "stadt", "hinein", "aber", "zunächst", "möchte", "ich", "deine", "ganz", "persönliche", "geschichte", "hören", "wie", "und", "wo", "bist", "du", "aufgewachsen, ", "wie", "bist", "du", "nach", "münster", "gekommen", "wie", "ging", "es", "im", "studium", "weiter", "und", "wie", "bist", "du", "in", "kontakt", "mit", "der", "frauenstraße"]
#tokenliste2 = ["danke", "volker", "dass", "du", "gekommen", "bist, ", "nachdem", "wir", "ja", "mehrere", "anläufe", "gemacht", "haben", "es", "geht", "um", "die", "70er", "80er", "jahre", "in", "münster", "um", "die", "auseinandersetzung", "um", "die", "frauenstraße", "um", "das", "studentische", "leben", "an", "der", "uni, ", "aber", "auch", "die", "auseinandersetzungen", "dort", "und", "was", "im", "grunde", "genommen", "in", "die", "stadt", "hinein", "wirkte", "aber", "zunächst", "möchte", "ich", "deine", "ganz", "persönliche", "geschichte", "hören", "wie", "und", "wo", "bist", "du", "aufgewachsen", "wie", "bist", "du", "nach", "münster", "gekommen", "ja", "und", "dann", "im", "grunde", "genommen", "wie", "ging", "es", "dann", "im", "studium", "weiter", "und", "wie", "bist", "du", "dann", "auch", "in", "kontakt", "mit", "der", "frauenstraße"]
b.berechneTransformationsmatrix (tokenliste1, tokenliste2)
# print(f"Tokendistanz: {b.berechneTransformationsmatrix (tokenliste1, tokenliste2)}")
# print (f"Länge Tokenliste 1: {len(tokenliste1)}")
# print (f"Länge Tokenliste 2: {len(tokenliste1)}")