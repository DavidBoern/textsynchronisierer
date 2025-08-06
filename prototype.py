from __future__ import annotations

# built-in
from collections import defaultdict
from itertools import zip_longest
from typing import Any, Sequence, TypeVar

import itertools
import pandas as pd
import pypandoc
import re

T = TypeVar('T')

class ASRExtrakt:
    def __init__(self,pfad):
        self.pfad = pfad
        self.df = pd.read_csv(pfad, sep='\t', header = 0)
        #Textinhalte des ASR-Extrakts befinden sich in der dritten Spalte. Lediglich diese muss analysiert/angepasst werden:
        self.asrExtraktText = self.df.iloc[:,2].astype(str).tolist()[1:]
        self.WortListeMitMarkern = self._erzeugeWortListeMitMarkern() 
    
    def _erzeugeWortListeMitMarkern(self):  
        wortListe = []
        for zeile in self.asrExtraktText:
            woerter = zeile.strip().split()
            wortListe.extend(woerter)
            wortListe.append('|')  # Zeilenende-Marker
        return wortListe
    
    def getWortlisteMitMarkern(self):
        #zum Test:
        # print (f"Die Anzahl der Wörter im Text beträgt {len(self.WortListeMitMarkern)}, die Anzahl der eindeutigen Wörter {len(list(set(self.WortListeMitMarkern)))}.")
        # print (self.WortListeMitMarkern)
        return self.WortListeMitMarkern
    
class ManuellesTranskript:
    def __init__(self,pfad):
        self.pfad = pfad
        self.wortListeOhnePraefixe = self._erzeugeWortListeOhnePraefixe(pfad)
       
    def _erzeugeWortListeOhnePraefixe(self,pfad):
        text = pypandoc.convert_file(pfad, 'plain')
        gesamtTextOhnePraefixe = re.sub(r"\b[A-Z]{2,3}_[A-Z]{2,3}\b","",text)
        wortListeOhnePraefixe = gesamtTextOhnePraefixe.split()
        # zum Test:
        # print (wortListeOhnePraefixe)
        return wortListeOhnePraefixe


    
    # def getWoerter(self):
    #     #zum Test:
    #     print (f"Die Anzahl der Wörter im Text beträgt {len(self.woerter)}, die Anzahl der eindeutigen Wörter {len(list(set(self.woerter)))}.")
    #     print (self.woerter)
    #     return self.woerter

class Textvorverarbeiter:
    def vorverarbeite (self, textListe):
        self.lowercase(textListe)
        self.umlauteNormalisieren(textListe)
        #zum Text:
        print (f"hier kommt die Textliste:{textListe}")
        return (textListe)

    def lowercase(self,t):
        for i in range(len(t)):
            t[i] = t[i].lower()
        return t
    
    def umlauteNormalisieren(self,t):
        umlautMap = {
        "ae": "ä", "oe": "ö", "ue": "ü", 
        "Ae": "Ä", "Oe": "Ö", "Ue": "Ü", 
        "ß": "ss"} 
        new_list = []
        for i in range(len(t)):
            for k, v in umlautMap.items():
                t[i] = t[i].replace(k, v)
        return t
        

    
#Klasse Levenshtein erbte ursprünglich von "__Base", diese Funktionalität ist jetzt in Klasse Levenshtein integriert
class Levenshtein:

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
    ) -> None:
        self.qval = qval
        self.test_func = test_func or self._ident

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

    def __call__(self, s1: Sequence[T], s2: Sequence[T]) -> int:
        s1, s2 = self._get_sequences(s1, s2)
        return self._cycled(s1, s2)

class Tokenuebertragung:
    def uebertrageToken(self, s1: Sequence[T], s2: Sequence[T], transformationsprotokoll: list[list[str]]):
        row_sequenz_anfangsindex = len(s1)-1
        print (f"row_sequenz_anfangsindex = {len(s1)-1}")
        row_matrix_anfangsindex = len([c for c in s1 if c != "|"]) # List comprehension
        col_anfangsindex = len(s2)  # Matrixindex geht bis len(s2), Index von s2 nur bis len(s2)-1
        self.syncSchritteAusfuehren (s1, s2, transformationsprotokoll, row_sequenz_anfangsindex, row_matrix_anfangsindex, col_anfangsindex)

        #nur zum Test:
        print (s1)      

    def syncSchritteAusfuehren (self, s1: Sequence[T], s2: Sequence[T], transformationsprotokoll: list[list[str]], row_sequenz_index, row_matrix_index, col_index):
        while row_sequenz_index >= 0:
            if s1[row_sequenz_index]=="|": row_sequenz_index -=1
            match transformationsprotokoll[row_matrix_index][col_index]:           
                case "e":
                    s1[row_sequenz_index] = s2 [col_index-1] # Wenn Wort z.B. 4 Zeichen lang, dann ist die letzte Stelle Index =3                  
                    print (f"e wird aufgerufen.Die Stelle {row_sequenz_index} wird durch {s2[col_index-1]} ersetzt.")
                    row_sequenz_index -= 1
                    row_matrix_index -= 1
                    col_index -= 1                    
                case "d":
                    s1.pop(row_sequenz_index)
                    row_sequenz_index -= 1
                    row_matrix_index -= 1
                    print (f"d wird aufgerufen.{row_sequenz_index} wird entfernt.")
                case "i":
                    s1.insert(row_sequenz_index+1, s2[col_index-1])
                    print (f"i wird aufgerufen. An der Stelle {row_sequenz_index+1} wird {s2[col_index-1]} eingefügt, eins mehr wäre ein {s2[col_index]} ")
                    col_index -=1
        #if row_sequenz == 0 or row_matrix == 0 or col == 0:
#            self.syncSchrittAusfuehren(s1, s2, transformationsprotokoll, row_sequenz_index, row_matrix_index, col_index)
        else:
            return s1
    
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

mt = ManuellesTranskript("ADG3149_01_01.odt")
tv = Textvorverarbeiter()
tv.vorverarbeite (mt.wortListeOhnePraefixe)

# asr = ASRExtrakt("ADG3149_01_01_de_speaker.csv")
# k = Kostenfunktion()
# k.berechneTokenDistanzen(mt.wortListeOhnePraefixe, asr.WortListeMitMarkern)

# print (asr.df.head)
#asr.getTokens()
# t = Tokenuebertragung()
# b = Levenshtein ()

# s1 = ["K","I","R","|","C","H","E"]
# s2 = ["K","R","O","N","E"]
# tp1 = b.berechneTransformationsmatrix (s1, s2)
# t.uebertrageToken(s1,s2,tp1)

# print(f"Tokendistanz: {b.berechneTransformationsmatrix (tokenliste1, tokenliste2)}")
# print (f"Länge Tokenliste 1: {len(tokenliste1)}")
# print (f"Länge Tokenliste 2: {len(tokenliste1)}")