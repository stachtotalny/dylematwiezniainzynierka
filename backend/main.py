import numpy as np
import asyncio
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Symulator Dylematu Więźnia API")

ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_API_KEY = os.getenv("SECRET_API_KEY", "domyslny-tajny-klucz-lokalny")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ParametrySymulacji(BaseModel):
    liczba_wysp: int = 5
    wielkosc_wyspy: int = 40
    liczba_epok: int = 100
    co_ile_kolonizacja: int = 10
    tempo_mutacji: float = 0.03
    szansa_na_mutacje: float = 0.2

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

class Agent():
    def __init__(self):
        self.wrodzony_stan = np.random.randn(1,4) * 0.1
        self.stan_wewnetrzny = np.copy(self.wrodzony_stan) 
        self.wagi_wejscia_rekurencyjne = np.random.randn(4,4) * 0.1
        self.wagi_wejscia = np.random.randn(2,4) * 0.1
        self.bias_wejscia = np.random.randn(1,4) * 0.1       
        self.wagi_wyjscia = np.random.randn(4,1) * 0.1
        self.bias_wyjscia = np.random.randn(1,1) * 0.1  
        
        self.struktura_wag = ['wrodzony_stan', 'wagi_wejscia_rekurencyjne', 
                              'wagi_wejscia', 'bias_wejscia', 
                              'wagi_wyjscia', 'bias_wyjscia']

    def resetuj_pamiec(self):
        self.stan_wewnetrzny = np.copy(self.wrodzony_stan)

    def krok(self, x):
        self.stan_wewnetrzny = np.tanh(np.dot(x, self.wagi_wejscia) + 
                                       np.dot(self.stan_wewnetrzny, self.wagi_wejscia_rekurencyjne) + 
                                       self.bias_wejscia)
        return sigmoid((np.dot(self.stan_wewnetrzny, self.wagi_wyjscia) + self.bias_wyjscia))

    def mutuj(self, tempo_mutacji=0.03, szansa_na_mutacje_wagi=0.2):
        for nazwa_wagi in self.struktura_wag:
            waga = getattr(self, nazwa_wagi)
            maska_mutacji = np.random.rand(*waga.shape) < szansa_na_mutacje_wagi
            szum = np.random.randn(*waga.shape) * tempo_mutacji
            setattr(self, nazwa_wagi, waga + (maska_mutacji * szum))

    def sklonuj(self):
        nowy = Agent()
        for nazwa_wagi in self.struktura_wag:
            setattr(nowy, nazwa_wagi, np.copy(getattr(self, nazwa_wagi)))
        return nowy 

    def krzyzuj_z(self, partner):
        potomek = Agent()
        for nazwa_wagi in self.struktura_wag:
            waga_rodzic1 = getattr(self, nazwa_wagi)
            waga_rodzic2 = getattr(partner, nazwa_wagi)
            maska = np.random.rand(*waga_rodzic1.shape) > 0.5
            setattr(potomek, nazwa_wagi, np.where(maska, waga_rodzic1, waga_rodzic2))
        return potomek


def rozegraj_gre(agent1, agent2, liczba_rund=100):
    agent1.resetuj_pamiec()
    agent2.resetuj_pamiec()
    wynik_agenta1 = 0 
    wynik_agenta2 = 0 
    ostatni_ruch_agenta1 = 1 
    ostatni_ruch_agenta2 = 1 
    ilosc_wspolprac = 0
    
    for _ in range(liczba_rund):
        wejscie_agenta1 = np.array([[ostatni_ruch_agenta1, ostatni_ruch_agenta2]])
        wejscie_agenta2 = np.array([[ostatni_ruch_agenta2, ostatni_ruch_agenta1]])
        
        praw_ruchu_agenta1 = agent1.krok(wejscie_agenta1).item()
        praw_ruchu_agenta2 = agent2.krok(wejscie_agenta2).item()
        
        ruch_agenta1 = 1 if praw_ruchu_agenta1 >= 0.5 else -1
        ruch_agenta2 = 1 if praw_ruchu_agenta2 >= 0.5 else -1
        
        if ruch_agenta1 == 1 and ruch_agenta2 == 1:
            wynik_agenta1 += 3 
            wynik_agenta2 += 3
            ilosc_wspolprac += 2
        elif ruch_agenta1 == -1 and ruch_agenta2 == 1:
            wynik_agenta1 += 5 
            wynik_agenta2 += 0
            ilosc_wspolprac += 1
        elif ruch_agenta1 == 1 and ruch_agenta2 == -1:
            wynik_agenta1 += 0 
            wynik_agenta2 += 5
            ilosc_wspolprac += 1
        elif ruch_agenta1 == -1 and ruch_agenta2 == -1:
            wynik_agenta1 += 1
            wynik_agenta2 += 1

        ostatni_ruch_agenta1 = ruch_agenta1 
        ostatni_ruch_agenta2 = ruch_agenta2 
        
    return wynik_agenta1, wynik_agenta2, ilosc_wspolprac, liczba_rund


def test_bota_laboratoryjnego(agent, typ_bota, liczba_rund=30):
    agent.resetuj_pamiec()
    ostatni_ruch_agenta = 1
    ostatni_ruch_bota = 1
    ruchy_agenta_historia = []
    grudger_aktywny = False
    
    for r_idx in range(liczba_rund):
        wejscie_agenta = np.array([[ostatni_ruch_agenta, ostatni_ruch_bota]])
        praw_ruchu = agent.krok(wejscie_agenta).item()
        ruch_agenta = 1 if praw_ruchu >= 0.5 else -1
        ruchy_agenta_historia.append('C' if ruch_agenta == 1 else 'D')
        if typ_bota == 'AllC':
            ruch_bota = 1
            
        elif typ_bota == 'AllD':
            ruch_bota = -1
            
        elif typ_bota == 'Grudger':
            if ruch_agenta == -1:
                grudger_aktywny = True
            ruch_bota = -1 if grudger_aktywny else 1
            
        elif typ_bota == 'Alternator':
            ruch_bota = 1 if r_idx % 2 == 0 else -1
            
        elif typ_bota == 'Joss':
            # Joss: Gra Wet za Wet (kopiuje ruch agenta), 
            # ale ma 10% szans na wbitą w plecy szpilę (niezależnie od wszystkiego).
            ruch_bota = ostatni_ruch_agenta
            if np.random.rand() < 0.10:
                ruch_bota = -1
                
        elif typ_bota == 'SneakyPacifist':
            # Zdradziecki Pacyfista: Zdradza TYLKO w pierwszej rundzie (r_idx == 0), 
            # potem do końca gry gra czyste C (1).
            ruch_bota = -1 if r_idx == 0 else 1
            
        ostatni_ruch_agenta = ruch_agenta
        ostatni_ruch_bota = ruch_bota
        
    return "".join(ruchy_agenta_historia)


def turniej_wyspowy(liczba_wysp=5, wielkosc_wyspy=40, liczba_epok=1000, co_ile_kolonizacja=10):
    wyspy = [[Agent() for _ in range(wielkosc_wyspy)] for _ in range(liczba_wysp)]
    
    for numer_epoki in range(liczba_epok):
        globalna_ilosc_wspolprac = 0
        globalna_ilosc_ruchow = 0
        sredni_fitness_wysp = []
        nowe_wyspy = []

        najlepszy_globalny_agent = None
        najwyzszy_globalny_fitness = -1

        for w_idx in range(liczba_wysp):
            populacja_wyspy = wyspy[w_idx]
            wyszukane_punkty = np.zeros(wielkosc_wyspy)
            wyszukane_ruchy = np.zeros(wielkosc_wyspy)

            for i in range(wielkosc_wyspy):
                for j in range(i + 1, wielkosc_wyspy):
                    p1, p2, wspolprace, ruchy = rozegraj_gre(populacja_wyspy[i], populacja_wyspy[j])
                    wyszukane_punkty[i] += p1
                    wyszukane_ruchy[i] += ruchy
                    wyszukane_punkty[j] += p2
                    wyszukane_ruchy[j] += ruchy
                    globalna_ilosc_wspolprac += wspolprace
                    globalna_ilosc_ruchow += ruchy

            fitness_wyspy = wyszukane_punkty / wyszukane_ruchy
            sredni_fitness_wysp.append(np.mean(fitness_wyspy))

            max_lokalny_idx = np.argmax(fitness_wyspy)
            if fitness_wyspy[max_lokalny_idx] > najwyzszy_globalny_fitness:
                najwyzszy_globalny_fitness = fitness_wyspy[max_lokalny_idx]
                najlepszy_globalny_agent = populacja_wyspy[max_lokalny_idx].sklonuj()

            nowa_populacja_wyspy = []
            najlepszy_lokalny = populacja_wyspy[np.argmax(fitness_wyspy)].sklonuj()
            nowa_populacja_wyspy.append(najlepszy_lokalny)

            def selekcja_turniejowa_lokalna():
                c1, c2 = np.random.choice(wielkosc_wyspy, size=2, replace=False)
                return populacja_wyspy[c1] if fitness_wyspy[c1] > fitness_wyspy[c2] else populacja_wyspy[c2]

            while len(nowa_populacja_wyspy) < wielkosc_wyspy:
                r1 = selekcja_turniejowa_lokalna()
                r2 = selekcja_turniejowa_lokalna()
                if np.random.rand() < 0.7:
                    dziecko = r1.krzyzuj_z(r2)
                else:
                    dziecko = r1.sklonuj()
                dziecko.mutuj(tempo_mutacji=parametry.tempo_mutacji, szansa_na_mutacje_wagi=parametry.szansa_na_mutacje)
                nowa_populacja_wyspy.append(dziecko)
                
            nowe_wyspy.append(nowa_populacja_wyspy)
            
        wyspy = nowe_wyspy

        if numer_epoki > 0 and numer_epoki % co_ile_kolonizacja == 0:
            najlepsza_wyspa = np.argmax(sredni_fitness_wysp)
            najgorsza_wyspa = np.argmin(sredni_fitness_wysp)
            
            if najlepsza_wyspa != najgorsza_wyspa:
                print(f"[KOLONIZACJA] Wyspa {najlepsza_wyspa} (Śr. Fitness: {sredni_fitness_wysp[najlepsza_wyspa]:.2f}) zastępuje wymarłą Wyspę {najgorsza_wyspa} (Śr. Fitness: {sredni_fitness_wysp[najgorsza_wyspa]:.2f})")
                for i in range(wielkosc_wyspy):
                    klon = wyspy[najlepsza_wyspa][i].sklonuj()
                    klon.mutuj(tempo_mutacji=parametry.tempo_mutacji * 1.5, szansa_na_mutacje_wagi=parametry.szansa_na_mutacje * 1.5)
                    wyspy[najgorsza_wyspa][i] = klon

        if numer_epoki % 5 == 0:
            procent_wspolpracy = (globalna_ilosc_wspolprac / (globalna_ilosc_ruchow * 2)) * 100
            print(f"Epoka: {numer_epoki:03d} | Średnie fitness wysp: {[round(f, 2) for f in sredni_fitness_wysp]} | Globalna Współpraca: {procent_wspolpracy:.2f}%")

        if numer_epoki % 5 == 0 and najlepszy_globalny_agent is not None:
            wynik_allc = test_bota_laboratoryjnego(najlepszy_globalny_agent, 'AllC')
            wynik_alld = test_bota_laboratoryjnego(najlepszy_globalny_agent, 'AllD')
            wynik_grudger = test_bota_laboratoryjnego(najlepszy_globalny_agent, 'Grudger')
            wynik_alternator = test_bota_laboratoryjnego(najlepszy_globalny_agent, 'Alternator')
            wynik_joss = test_bota_laboratoryjnego(najlepszy_globalny_agent, 'Joss')
            wynik_sneaky = test_bota_laboratoryjnego(najlepszy_globalny_agent, 'SneakyPacifist')
            
            print("\n" + "="*85)
            print(f"[PROFIL PSYCHOLOGICZNY - TEST 30 RUND] Epoka: {numer_epoki:03d} | Fitness: {najwyzszy_globalny_fitness:.2f}")
            print(f"  -> Vs Zawsze Współpracuj (AllC):  {wynik_allc}")
            print(f"  -> Vs Zawsze Zdradzaj (AllD):     {wynik_alld}")
            print(f"  -> Vs Złośliwy Bot (Grudger):     {wynik_grudger}")
            print(f"  -> Vs Alternator (Zdradza co 2):  {wynik_alternator}")
            print(f"  -> Vs Joss (Wet za Wet + 10% D):  {wynik_joss}")
            print(f"  -> Vs Cwaniak (Zdrada -> AllC):   {wynik_sneaky}")
            print("="*85 + "\n")

@app.post("/api/symulacja")
async def uruchom_symulacje(parametry: ParametrySymulacji, x_api_key: str = Header(None)):
    if x_api_key != SECRET_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Brak autoryzacji: Nieprawidłowy lub brakujący klucz API."
        )
    async def generator_epok():
        wyspy = [[Agent() for _ in range(parametry.wielkosc_wyspy)] for _ in range(parametry.liczba_wysp)]

        for numer_epoki in range(parametry.liczba_epok):
            globalna_ilosc_wspolprac = 0
            globalna_ilosc_ruchow = 0
            
            sredni_fitness_wysp = []
            statystyki_wysp = [] 
            nowe_wyspy = []
            
            najlepszy_globalny_agent = None
            najwyzszy_globalny_fitness = -1

            for w_idx in range(parametry.liczba_wysp):
                populacja_wyspy = wyspy[w_idx]
                wyszukane_punkty = np.zeros(parametry.wielkosc_wyspy)
                wyszukane_ruchy = np.zeros(parametry.wielkosc_wyspy)
                wspolprace_na_wyspie = 0 

                for i in range(parametry.wielkosc_wyspy):
                    for j in range(i + 1, parametry.wielkosc_wyspy):
                        p1, p2, wspolprace, ruchy = rozegraj_gre(populacja_wyspy[i], populacja_wyspy[j])
                        wyszukane_punkty[i] += p1
                        wyszukane_ruchy[i] += ruchy
                        wyszukane_punkty[j] += p2
                        wyszukane_ruchy[j] += ruchy
                        
                        wspolprace_na_wyspie += wspolprace
                        globalna_ilosc_wspolprac += wspolprace
                        globalna_ilosc_ruchow += ruchy

                fitness_wyspy = wyszukane_punkty / wyszukane_ruchy
                sredni_fitness_wyspy = float(np.mean(fitness_wyspy))
                sredni_fitness_wysp.append(sredni_fitness_wyspy)
                
                suma_ruchow_wyspy = np.sum(wyszukane_ruchy)
                procent_wspolpracy_wyspy = (wspolprace_na_wyspie / suma_ruchow_wyspy) * 100 if suma_ruchow_wyspy > 0 else 0

                statystyki_wysp.append({
                    "id": w_idx,
                    "fitness": round(sredni_fitness_wyspy, 3),
                    "wspolpraca_procent": round(float(procent_wspolpracy_wyspy), 2)
                })

                max_lokalny_idx = np.argmax(fitness_wyspy)
                if fitness_wyspy[max_lokalny_idx] > najwyzszy_globalny_fitness:
                    najwyzszy_globalny_fitness = fitness_wyspy[max_lokalny_idx]
                    najlepszy_globalny_agent = populacja_wyspy[max_lokalny_idx].sklonuj()

                nowa_populacja_wyspy = []
                nowa_populacja_wyspy.append(najlepszy_globalny_agent.sklonuj())

                def selekcja_turniejowa_lokalna():
                    c1, c2 = np.random.choice(parametry.wielkosc_wyspy, size=2, replace=False)
                    return populacja_wyspy[c1] if fitness_wyspy[c1] > fitness_wyspy[c2] else populacja_wyspy[c2]

                while len(nowa_populacja_wyspy) < parametry.wielkosc_wyspy:
                    r1 = selekcja_turniejowa_lokalna()
                    r2 = selekcja_turniejowa_lokalna()
                    dziecko = r1.krzyzuj_z(r2) if np.random.rand() < 0.7 else r1.sklonuj()
                    dziecko.mutuj(tempo_mutacji=0.03, szansa_na_mutacje_wagi=0.2)
                    nowa_populacja_wyspy.append(dziecko)

                nowe_wyspy.append(nowa_populacja_wyspy)

            wyspy = nowe_wyspy
            
            zdarzenie_kolonizacji = None
            if numer_epoki > 0 and numer_epoki % parametry.co_ile_kolonizacja == 0:
                najlepsza_wyspa = int(np.argmax(sredni_fitness_wysp))
                najgorsza_wyspa = int(np.argmin(sredni_fitness_wysp))
                
                if najlepsza_wyspa != najgorsza_wyspa:
                    zdarzenie_kolonizacji = {
                        "zwyciezca": najlepsza_wyspa,
                        "przegrany": najgorsza_wyspa
                    }
                    for i in range(parametry.wielkosc_wyspy):
                        klon = wyspy[najlepsza_wyspa][i].sklonuj()
                        klon.mutuj(tempo_mutacji=0.05, szansa_na_mutacje_wagi=0.3)
                        wyspy[najgorsza_wyspa][i] = klon

            procent_wspolpracy_globalny = (globalna_ilosc_wspolprac / (globalna_ilosc_ruchow * 2)) * 100
            
            dane_epoki = {
                "epoka": numer_epoki + 1,
                "sredni_fitness_globalny": round(float(np.mean(sredni_fitness_wysp)), 3),
                "wspolpraca_procent_globalna": round(float(procent_wspolpracy_globalny), 2),
                "statystyki_wysp": statystyki_wysp,
                "zdarzenie_kolonizacji": zdarzenie_kolonizacji
            }

            if (numer_epoki + 1) % 10 == 0 and najlepszy_globalny_agent:
                dane_epoki["profil_psychologiczny"] = {
                    "AllC": test_bota_laboratoryjnego(najlepszy_globalny_agent, 'AllC'),
                    "AllD": test_bota_laboratoryjnego(najlepszy_globalny_agent, 'AllD'),
                    "Grudger": test_bota_laboratoryjnego(najlepszy_globalny_agent, 'Grudger'),
                    "Alternator": test_bota_laboratoryjnego(najlepszy_globalny_agent, 'Alternator'),
                    "Joss": test_bota_laboratoryjnego(najlepszy_globalny_agent, 'Joss'),
                    "SneakyPacifist": test_bota_laboratoryjnego(najlepszy_globalny_agent, 'SneakyPacifist')
                }


            yield f"data: {json.dumps(dane_epoki)}\n\n"
            await asyncio.sleep(0.001)

    return StreamingResponse(generator_epok(), media_type="text/event-stream")



#testowa zmiana do ponownego wdrożenia 
