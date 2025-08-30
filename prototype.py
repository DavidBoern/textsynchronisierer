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
    """Liest ASR-Extrakt ein und erzeugt eine Wortliste 
    mit Zeilenende-Markern."""
    def __init__(self,pfad):
        self.pfad = pfad
        self.df = pd.read_csv(pfad, sep='\t', header = 0)
        # Transkriptionstext befindet sich in Spalte 3
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
    """Liest manuelles Transkript aus ODT ein, 
    entfernt Sprecherkürzel und erzeugt Wortliste."""
    def __init__(self,pfad):
        self.pfad = pfad
        self.wortListeOhnePraefixe = self._erzeugeWortListeOhnePraefixe(pfad)
        self.originalWortListeOhnePraefixe = self.wortListeOhnePraefixe.copy()
       
    def _erzeugeWortListeOhnePraefixe(self,pfad):
        text = pypandoc.convert_file(pfad, 'plain')
        zeilen = text.splitlines()     
        #Ggf. im Dokument vorhandene Überschrift wird entfernt.
        if not re.match(r"\b[A-Z]{2,3}_[A-Z]{2,3}\b", zeilen[0]):
            zeilen.pop(0)
        text = "\n".join(zeilen)
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
        textListe = self._punktuationEntfernen(textListe)
        return (textListe)

    def _lowercase(self,t):
        for i in range(len(t)):
            t[i] = t[i].lower()
        return t
    
    def _umlauteNormalisieren(self,t):
        umlautMap = {
        "ae": "ä", "oe": "ö", "ue": "ü",  
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
    
    def _punktuationEntfernen (self, wortListe):
    # Token, die ausschließlich aus Satzzeichen bestehen, 
    # bleiben als leere Element in der Wortliste, um Indexpositionen beizubehalten. 
        return [t.strip(string.punctuation.replace("|", "")) for t in wortListe]
              
class Levenshtein:
    """Implementierung des Levenshtein-Algorithmus auf Basis der textdistance-Library"""
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
        """Erstellt Transformationsmatrix zur Rekonstruktion der Editierschritte 
        (nicht, wie beim Levenshtein-Algorithmus üblich, Distanzwert)."""
        STANDARD_ERSETZUNGSKOSTEN = 4
        # hoher Wert, um Ersetzungen von Begriffen, die sich in den zu vergleichenden 
        # Textdateien in unterschiedlichen Bereichen befinden, zu vermeiden.
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
        rMatrix = 1
        for rSequenz in range(len(s1)):
            if s1[rSequenz] == "|": 
                continue          
            prev, cur = cur, [rMatrix] + [0] * (cols - 1)
            for c in range(1, cols):              
                deletion = prev[c] + 1
                insertion = cur[c - 1] + 1
                gleich = self.test_func(s1[rSequenz], s2[c - 1])
                if gleich: ersetzKosten = 0
                else: 
                    ersetzKosten = kostenfunktion.get((s1[rSequenz], s2[c - 1]), STANDARD_ERSETZUNGSKOSTEN)
                    #ersetzKosten = STANDARD_ERSETZUNGSKOSTEN
                edit = prev[c - 1] + ersetzKosten
                cur[c] = min(edit, deletion, insertion)
                if cur[c] == edit:
                    transformationsprotokoll[rMatrix][c] = "e"
                elif cur[c] == deletion:
                    transformationsprotokoll[rMatrix][c] = "d"
                else:
                    transformationsprotokoll[rMatrix][c] = "i"
            rMatrix +=1
        return transformationsprotokoll

class Tokenuebertragung:
    def uebertrageToken(self, s1: Sequence[T], s2: Sequence[T], transformationsprotokoll: list[list[str]]):
        row_sequenz_anfangsindex = len(s1)-1
        row_matrix_anfangsindex = len([c for c in s1 if c != "|"])
        col_anfangsindex = len(s2)
        self._syncSchritteAusfuehren (s1, s2, transformationsprotokoll, row_sequenz_anfangsindex, row_matrix_anfangsindex, col_anfangsindex)
        return s1
        
    def _syncSchritteAusfuehren (self, asr: Sequence[T], mt: Sequence[T], transformationsprotokoll: list[list[str]], row_sequenz_index, row_matrix_index, col_index):
        while row_sequenz_index >= 0:
            if asr[row_sequenz_index]=="|": row_sequenz_index -=1
            """Um Transformationspfad zu identifizieren, wird Matrix rückwärts durchlaufen.  
            Priorität bei gleichen Kosten: Ersetzung>Löschung>Einfügung."""   
            match transformationsprotokoll[row_matrix_index][col_index]:                        
                case "e":
                    asr[row_sequenz_index] = mt [col_index-1] 
                    row_sequenz_index -= 1
                    row_matrix_index -= 1
                    col_index -= 1                    
                case "d":
                    asr.pop(row_sequenz_index)
                    row_sequenz_index -= 1
                    row_matrix_index -= 1
                case "i":
                    asr.insert(row_sequenz_index+1, mt[col_index-1])
                    col_index -=1
        else:
            return asr
    
    def asrZeilenumbruecheProtokollieren (self,asr):
        asrUmbruchstellen = []
        for i in range(len(asr)):
            if asr[i] == "|":
                asrUmbruchstellen.append (i)
        return asrUmbruchstellen
  
class Kostenfunktion():
    """Berechnet gewichtete Ersetzungskosten für Token, die sich
    in den beiden Dateien (ASR-Extrakt und Manuellem Transkript) 
    in ähnlichen Bereichen befinden."""
    def __init__(self):
        self.aehnlichkeitsmass = {}
    
    def _normiereKostenFunktion(self, dict_Werte):
        """Normiert Kosten auf Mittelwert 1."""
        faktor = len(dict_Werte)/sum(dict_Werte.values())
        for key in dict_Werte:
            dict_Werte[key]=dict_Werte[key]*faktor
        return dict_Werte       
              
    def _erstelleTokenpaare(self, gesamtListe1, gesamtListe2):
        """Erzeugt die Tokenpaare, für die gewichtete Ersetzungskosten berechnet werden."""
        MIN_GROESSE_TESTSET_1 = 5   # abweichende Setgrößen werden im Rahmen der Evaltuation erprobt.
        anzahlTestSets = int(len(gesamtListe1)/MIN_GROESSE_TESTSET_1)
        groesseSet1 = float(len(gesamtListe1) / anzahlTestSets)
        groesseSet2 = float(len(gesamtListe2) / anzahlTestSets)
        # Um harte Setgrenzen zu verhindern, wird überlappend iteriert.
        testSets =[]
        for i in range (2*anzahlTestSets):
            testSets.append (gesamtListe1[int(0.5*i*groesseSet1):int((0.5*i+1)*groesseSet1)] + gesamtListe2[int(0.5*i*groesseSet2):int((0.5*i+1)*groesseSet2)])
        for i in range(len(testSets)):
            testSets[i]=sorted (set(testSets[i]))
        tokenKombinationen = set ()
        for s in testSets:          
            for kombination in itertools.combinations(s, 2):
                if "|" not in kombination[0] and "|" not in kombination[1]:
                    tokenKombinationen.add(kombination)
                    tokenKombinationen.add((kombination[1], kombination[0]))
        tokenKombinationen = tuple (tokenKombinationen)
        return tokenKombinationen               

    def berechneTokenDistanzen(self, gesamtListe1, gesamtListe2):
        levenshtein = Levenshtein()
        tokenKombinationen = self._erstelleTokenpaare(gesamtListe1,gesamtListe2)
        for tupel in tokenKombinationen:
            self.aehnlichkeitsmass.update({tupel:(levenshtein._cycled(tupel[0], tupel[1]))/(max(len(tupel[0]),len(tupel[1])))})        
        self.aehnlichkeitsmass = self._normiereKostenFunktion(self.aehnlichkeitsmass)
        return self.aehnlichkeitsmass
     
class ASRKorrektur:
    """Ersetzt den Text im ASR-Transkript durch die korrigierte Wortliste."""
    def _zeilentextErstellen(self, umbrueche, wortliste, asr):
        teile, start = [], 0
        # Eingefügte Zeilenend-Marker verschieben die Indexpositionen. 
        # Dies wird hier berücksichtigt.
        umbruecheModifiziert = []
        for u in umbrueche:
            umbruecheModifiziert.append (u-(umbrueche.index(u)+1))
        for stop in umbruecheModifiziert:
            teile.append(" ".join(wortliste[start:stop+1]))
            start = stop + 1
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

    asrVergleichsText = tv.vorverarbeite (asr.wortListeMitMarkern)
    mtVergleichsText = tv.vorverarbeite (mt.wortListeOhnePraefixe)

    k = Kostenfunktion()
    aehnlichkeitsmass = k.berechneTokenDistanzen (mtVergleichsText, asrVergleichsText)

    l = Levenshtein()
    transformationsmatrix = l.berechneTransformationsmatrix(asrVergleichsText, mtVergleichsText, aehnlichkeitsmass) 

    t = Tokenuebertragung ()
    korrigiertesASR = t.uebertrageToken(asrVergleichsText, mtVergleichsText, transformationsmatrix)

    zeilenumbrueche = t.asrZeilenumbruecheProtokollieren(korrigiertesASR)

    csv = ASRKorrektur()
    csv._zeilentextErstellen (zeilenumbrueche, mt.originalWortListeOhnePraefixe, asr.df)

if __name__ == "__main__":
    main()