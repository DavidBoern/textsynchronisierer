#der Levenshtein-Algorithmus ist übernommen von der Python Library "TextDistance"  
from __future__ import annotations

# built-in
from collections import defaultdict
from itertools import zip_longest
from typing import Any, Sequence, TypeVar

import itertools
import pandas as pd
import pypandoc
import os
import re
import string

T = TypeVar('T')


class ASRExtrakt:
    def __init__(self,pfad):
        self.pfad = pfad
        self.df = pd.read_csv(pfad, sep='\t', header = 0)
        #Die Textinhalte des ASR-Extrakts befinden sich in der dritten Spalte der CSV-Datei. Für die weiteren Schritte des Textvergleichs muss diese ausgelesen werden.
        self.asrExtraktText = self.df.iloc[:,2].astype(str).tolist()[0:]
        self.wortListeMitMarkern = self._erzeugeWortListeMitMarkern() 
    
    def _erzeugeWortListeMitMarkern(self):  
        wortListe = []
        for zeile in self.asrExtraktText:
            woerter = zeile.strip().split()
            wortListe.extend(woerter)
            wortListe.append('|')  # Zeilenende-Marker
        return wortListe
        
class ManuellesTranskript:
    def __init__(self,pfad):
        self.pfad = pfad
        self.wortListeOhnePraefixe = self._erzeugeWortListeOhnePraefixe(pfad)
        self.originalWortListeOhnePraefixe = self.wortListeOhnePraefixe.copy()   # Kopie, die im weiteren Programmablauf unverändert bleibt.
       
    def _erzeugeWortListeOhnePraefixe(self,pfad):
        text = pypandoc.convert_file(pfad, 'plain')
        gesamtTextOhnePraefixe = re.sub(r"\b[A-Z]{2,3}_[A-Z]{2,3}\b","",text)
        wortListeOhnePraefixe = gesamtTextOhnePraefixe.split()
        return wortListeOhnePraefixe

class Textvorverarbeiter:
    def vorverarbeite (self, textListe):
        textListe = self._lowercase(textListe)
        textListe = self._umlauteNormalisieren(textListe)
        textListe = self._zahlenNormalisieren(textListe)
        textListe = self._abkuerzungenNormalisieren(textListe)
        textListe = self._waehrungszeichenNormalisieren(textListe)
        textListe = self.punktuationEntfernen(textListe)
        return (textListe)

    def _lowercase(self,t):
        for i in range(len(t)):
            t[i] = t[i].lower()
        return t
    
    def _umlauteNormalisieren(self,t):
        umlautMap = {
        "ae": "ä", "oe": "ö", "ue": "ü",  # wegen vorgelagertem lowercase ist Vergleich von Kleinbuchstagen ausreichend. Fehler wie die Umwandlung in "fraünstrasse" können vernachlässigt werden, weil Vorverarbeitungsschritte lediglich temporär sind, und derartige Fehler für den Textvergleich nicht besonders relevant sind.  
        "ß": "ss"} 
        for i in range(len(t)):
            for k, v in umlautMap.items():
                t[i] = t[i].replace(k, v)
        return t
          
    def _tokenMitZahlenMapVergleichen (self, token): 
        ZAHLENMAP = {
        "eins":"1", "zwei": "2", "drei": "3", "vier": "4", "fünf": "5", "sechs": "6", "sieben": "7", "acht": "8", "neun": "9", "zehn": "10", "elf": "11", "zwölf": "12",
        "erste": "1.", "erster": "1.", "erstes": "1.", "erstens": "1.",
        "zweite": "2.", "zweiter": "2.", "zweites": "2.", "zweitens": "2.",
        "dritte": "3.", "dritter": "3.", "drittes": "3.", "drittens": "3.",
        "vierte": "4.", "vierter": "4.", "viertes": "4.", "viertens": "4.",
        "fünfte": "5.", "fünfter": "5.", "fünftes": "5.", "fünftens": "5.",
        "sechste": "6.", "sechster": "6.", "sechstes": "6.", "sechstens": "6.",
        "siebte": "7.", "siebter": "7.", "siebtes": "7.", "siebtens": "7.",
        "achte": "8.", "achter": "8.", "achtes": "8.", "achtens": "8.",
        "neunte": "9.", "neunter": "9.", "neuntes": "9.", "neuntens": "9.",
        "zehnte": "10.", "zehnter": "10.", "zehntes": "10.", "zehntens": "10.",
        "elfte": "11.", "elfter": "11.", "elftes": "11.", "elftens": "11.",
        "zwölfte": "12.", "zwölfter": "12.", "zwölftes": "12.", "zwölftens": "12."
        }
        return ZAHLENMAP.get(token, token)
    
    def _zahlenNormalisieren(self,wortListe):
        return [self._tokenMitZahlenMapVergleichen(t) for t in wortListe]
         
    def _waehrungszeichenNormalisieren(self,t):
        waehrungszeichenMap = {
        "dollar": "$", "dollars": "$", "euro": "€", "euros": "€"} 
        for i in range(len(t)):
            for k, v in waehrungszeichenMap.items():
                t[i] = t[i].replace(k, v)
        return t
    
    def _tokenMitAbkuerzungsMapVergleichen (self, token): 
        ABKUERZUNGSMAP = {
            "z.b.": "zum Beispiel",
            "v.a.": "vor allem",
            "u.a.": "unter anderem",
            "d.h.": "das heißt",
            "bzw.": "beziehungsweise",
            "usw.": "und so weiter",
            "ca.": "circa",
            "etc.": "et cetera",
            "sog.": "sogenannt",
            "mfg": "mit freundlichen Grüßen"
        }
        return ABKUERZUNGSMAP.get(token, token)
    
    def _abkuerzungenNormalisieren(self,wortListe):
        return [self._tokenMitAbkuerzungsMapVergleichen(t) for t in wortListe]
    
# in der folgenden Methode bleiben Elemente, die lediglich aus Satzzeichen bestehen, als leere Elemente in der Liste. Sie lässt somit (wie sämtliche Vorverarbeitungsschritte) die Länge der Wortliste (und auch die einzelnen Indexpositionen) unverändert. Das erleichtert die später vorgesehene Rückabwicklung der Vorverarbeitungsschritte: 
    def punktuationEntfernen (self, wortListe):
        return [t.strip(string.punctuation.replace("|", "")) for t in wortListe]
              
# Klasse Levenshtein erbt in der textdistance-Library von "__Base". Diese Funktionalität isthier in der Klasse Levenshtein integriert
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
      
    def berechneTransformationsmatrix (self, s1: Sequence[T], s2: Sequence[T], kostenfunktion: dict[tuple[T, T], float]):
        rows = len([c for c in s1 if c != "|"]) + 1
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
                gleich = self.test_func(s1[r_sequenz], s2[c - 1])
                if gleich: ersetzKosten = 0
                else: 
                    ersetzKosten = kostenfunktion.get((s1[r_sequenz], s2[c - 1]), 3)
                edit = prev[c - 1] + ersetzKosten
                cur[c] = min(edit, deletion, insertion)
                if cur[c] == edit:
                    transformationsprotokoll[r_matrix][c] = "e"
                elif cur[c] == deletion:
                    transformationsprotokoll[r_matrix][c] = "d"
                else:
                    transformationsprotokoll[r_matrix][c] = "i"
            r_matrix +=1
        return transformationsprotokoll

class Tokenuebertragung:
    def uebertrageToken(self, s1: Sequence[T], s2: Sequence[T], transformationsprotokoll: list[list[str]]):
        row_sequenz_anfangsindex = len(s1)-1
        #print (f"row_sequenz_anfangsindex = {len(s1)-1}")
        row_matrix_anfangsindex = len([c for c in s1 if c != "|"]) # List comprehension
        col_anfangsindex = len(s2)  # Matrixindex geht bis len(s2), Index von s2 nur bis len(s2)-1
        self._syncSchritteAusfuehren (s1, s2, transformationsprotokoll, row_sequenz_anfangsindex, row_matrix_anfangsindex, col_anfangsindex)
        return s1
        #zum Test:
        #print (s1)      

    def _syncSchritteAusfuehren (self, asr: Sequence[T], mt: Sequence[T], transformationsprotokoll: list[list[str]], row_sequenz_index, row_matrix_index, col_index):
        while row_sequenz_index >= 0:
            if asr[row_sequenz_index]=="|": row_sequenz_index -=1
            match transformationsprotokoll[row_matrix_index][col_index]:           
                case "e":
                    asr[row_sequenz_index] = mt [col_index-1] # Wenn Wort z.B. 4 Zeichen lang, dann ist die letzte Stelle Index =3                  
                    #print (f"e wird aufgerufen.Die Stelle {row_sequenz_index} wird durch {s2[col_index-1]} ersetzt.")
                    row_sequenz_index -= 1
                    row_matrix_index -= 1
                    col_index -= 1                    
                case "d":
                    asr.pop(row_sequenz_index)
                    row_sequenz_index -= 1
                    row_matrix_index -= 1
                    #print (f"d wird aufgerufen.{row_sequenz_index} wird entfernt.")
                case "i":
                    asr.insert(row_sequenz_index+1, mt[col_index-1])
                    #print (f"i wird aufgerufen. An der Stelle {row_sequenz_index+1} wird {s2[col_index-1]} eingefügt, eins mehr wäre ein {s2[col_index]} ")
                    col_index -=1
        #if row_sequenz == 0 or row_matrix == 0 or col == 0:
#            self.syncSchrittAusfuehren(s1, s2, transformationsprotokoll, row_sequenz_index, row_matrix_index, col_index)
        else:
            return asr
    
    def _zeilenumbruecheProtokollieren (self,asr):
        umbruchstellen = []
        for i in range(len(asr)):
            if asr[i] == "|":
                umbruchstellen.append (i)
        return umbruchstellen
  
class Kostenfunktion():
    def __init__(self):
        self.aehnlichkeitsmass = {}

    def _normiereKostenFunktion(self, dict_Werte):
        faktor = len(dict_Werte)/sum(dict_Werte.values())
        for key in dict_Werte:
            dict_Werte[key]=dict_Werte[key]*faktor
        return dict_Werte       
    
    # Um den Rechenaufwand zu minimieren, werden zur Integration gewichteter Ersetzungskosten lediglich Tokenpaare betrachtet, die sich in benachbarten Bereichen der beiden Tokensequenzen befinden. Zudem lässt sich so realisieren, dass "weit entfernte" Ersetzungen mit hohen Kosten verbunden sind. 
    # alte Methode 
    # def _erstelleTokenpaare(self, token_List1, token_List2):
    #     eindeutigeToken = sorted(set(token_List1 + token_List2))
    #     tokenKombinationen = itertools.combinations(eindeutigeToken,2)
    #     return tokenKombinationen                              

              
    def _erstelleTokenpaare(self, gesamtListe1, gesamtListe2):
        MINGROESSE_TESTSET1 = 40
        anzahlTestSets = int(len(gesamtListe1)/MINGROESSE_TESTSET1)
        print (f"anzahlTestSets= {anzahlTestSets}")
        print (f"len(gesamtListe1) = {len(gesamtListe1)}")
        groesseSet1 = float(len(gesamtListe1) / anzahlTestSets)
        groesseSet2 = float(len(gesamtListe2) / anzahlTestSets)
        print (f"groesseSet1 + groesseSet2 = {groesseSet1}, {groesseSet2}")
        # um harte Setgrenzen zu verhindern wird überlappend iteriert.
        testSets =[]
        for s in testSets:
        for kombination in itertools.combinations(s, 2):
            # 1. Nur aufnehmen, wenn kein "|" enthalten ist
            if "|" not in kombination[0] and "|" not in kombination[1]:
                # 2. Normal und gespiegelte Reihenfolge aufnehmen
                tokenKombinationen.add(kombination)
                tokenKombinationen.add((kombination[1], kombination[0]))
        tokenKombinationen = tuple (tokenKombinationen)
        print (f"Hier die TokenKombinationen: {tokenKombinationen}")
        return tokenKombinationen               

    def berechneTokenDistanzen(self, gesamtListe1, gesamtListe2):
        levenshtein = Levenshtein()
        tokenKombinationen = self._erstelleTokenpaare(gesamtListe1,gesamtListe2)
        for tupel in tokenKombinationen:
            self.aehnlichkeitsmass.update({tupel:(levenshtein._cycled(tupel[0], tupel[1]))/(max(len(tupel[0]),len(tupel[1])))})        
        self.aehnlichkeitsmass = self._normiereKostenFunktion(self.aehnlichkeitsmass)
        #zum Test:
        #print (dict(sorted(self.aehnlichkeitsmass.items(), key=lambda item: item[1])))
        #print (self.aehnlichkeitsmass)
        return self.aehnlichkeitsmass

class ASRKorrektur:
    def _zeilentextErstellen(self, umbrueche, wortliste, asr):
        teile, start = [], 0
        umbruecheModifiziert = []
        for u in umbrueche:
            umbruecheModifiziert.append (u-(umbrueche.index(u)+1))
        print (umbruecheModifiziert)
        for stop in umbruecheModifiziert: # + [len(wortliste)-1]:
            teile.append(" ".join(wortliste[start:stop+1]))
            start = stop + 1
        print (f"teile = {teile}")
        print (f"ASR = {asr}")        
        for i in range(len(teile)):
            asr.iat[i, 2] = teile[i]        
        asr.to_csv("output.csv", sep="\t", index=False)

def dateiEinlesen (prompt, regEx):
    while True:
        pfad = input(prompt)
        if not re.search(regEx, pfad, re.IGNORECASE):
            print("Falsche Dateiendung.")
            continue
        if not os.path.isfile(pfad):
            print("Datei existiert nicht.")
            continue
        return pfad

def main():
    csvPfad = dateiEinlesen("Pfad zur CSV-Datei eingeben: ", r"\.csv$")
    odtPfad = dateiEinlesen("Pfad zur ODT-Datei eingeben: ", r"\.odt$")

    asr = ASRExtrakt(csvPfad)
    mt = ManuellesTranskript(odtPfad)

    tv = Textvorverarbeiter()

    #print (f"Textliste des ASR-Extrakts OHNE Vorverarbeitung:\n {asr.wortListeMitMarkern} \nLänge: {len(asr.wortListeMitMarkern)}")
    asrVergleichsText = tv.vorverarbeite (asr.wortListeMitMarkern)
    #print (f"Textliste des  ASR-Extrakts MIT Vorverarbeitung:\n {asrVergleichsText} \nLänge: {len(asrVergleichsText)}")

    #print (f"Textliste des manuellen Transkripts OHNE Vorverarbeitung:\n {mt.wortListeOhnePraefixe} \nLänge: {len(mt.wortListeOhnePraefixe)}")
    mtVergleichsText = tv.vorverarbeite (mt.wortListeOhnePraefixe)
    #print (f"Textliste des manuellen Transkripts MIT Vorverarbeitung:\n {mtVergleichsText} \nLänge: {len(mtVergleichsText)}")

    # Kostenfunktion erstellen (evtl. nicht sinnvoll: rechenintensiv und geringer Mehrwert. Erstmal weglassen ):
    k = Kostenfunktion()
    aehnlichkeitsmass = k.berechneTokenDistanzen (mtVergleichsText, asrVergleichsText)
    # #zum Test
    #print(f"Hier die Kostenfunktion:{k.aehnlichkeitsmass}")

    # Transformationsmatrix berechnen:
    l = Levenshtein()
    transformationsmatrix = l.berechneTransformationsmatrix(asrVergleichsText, mtVergleichsText, aehnlichkeitsmass) 

    t = Tokenuebertragung ()
    korrigiertesASR = t.uebertrageToken(asrVergleichsText, mtVergleichsText, transformationsmatrix)
    # zum Test:
    print(f"Hier zum Test das korrigierte ASR, allerdings noch mit Pipe statt Zeilenumbruch und durch Vorverarbeitungssschritte modifiziert: {korrigiertesASR}")

    # zum Test:
    zeilenumbrueche = t._zeilenumbruecheProtokollieren(korrigiertesASR)
    print (f"Stellen mit Zeilenumbrüchen: {zeilenumbrueche}")

    csv = ASRKorrektur()
    csv._zeilentextErstellen (zeilenumbrueche, mt.originalWortListeOhnePraefixe, asr.df)

if __name__ == "__main__":
    main()