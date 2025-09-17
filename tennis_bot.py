#!/usr/bin/env python3
"""
TennisBot - A bot that provides tennis hints and tips
"""

import random
import sys

class TennisBot:
    def __init__(self):
        self.hints = [
            "Pidä mailasta tiukasti kiinni, mutta älä jännittele rannettas liikaa.",
            "Katso palloa aina mailaniskuun asti.",
            "Pyri saamaan jalat liikkeessä ennen iskua.",
            "Keskity vastustajan heikkouksiin ja pelaa niihin.",
            "Harjoittele palvelua säännöllisesti - se on tärkein isku.",
            "Pidä kehon painopiste alhaalla liikkuessasi.",
            "Älä yritä iskeä liian kovaa - tarkkuus on tärkeämpää.",
            "Opettele käyttämään koko kenttää hyväksesi.",
            "Pysyttele baseline-keskustan lähellä perusasemassa.",
            "Hengitä tasaisesti ja pysy rauhallisena paineen alla."
        ]
        
        self.tips = [
            "Lämittele aina ennen peliä vammojen välttämiseksi.",
            "Juo vettä säännöllisesti pelin aikana.",
            "Käytä aurinkosuojaa ulkona pelatessa.",
            "Valitse oikeat kengät kentän pintaan sopiviksi.",
            "Lepuuta vartaloa perien välissä.",
            "Opiskele sääntöjä huolellisesti ennen kilpailuja.",
            "Pidä mailoistasi hyvää huolta ja vaihda kielet säännöllisesti.",
            "Tee venyttelyjä pelin jälkeen.",
            "Seuraa tennistä televisiosta oppiaksesi ammattilaisilta.",
            "Pelaa erilaisten vastustajien kanssa parantaaksesi taitojasi."
        ]

    def get_random_hint(self):
        """Palauttaa satunnaisen tennisvihjeen"""
        return random.choice(self.hints)

    def get_random_tip(self):
        """Palauttaa satunnaisen tennisvinkin"""
        return random.choice(self.tips)

    def get_all_hints(self):
        """Palauttaa kaikki vihjeet"""
        return self.hints

    def get_all_tips(self):
        """Palauttaa kaikki vinkit"""
        return self.tips

    def run_interactive(self):
        """Käynnistää interaktiivisen tilan"""
        print("🎾 Tervetuloa TennisBot:iin! 🎾")
        print("Komennot:")
        print("  'vihje' tai 'hint' - Saa satunnaisen pelivihjeen")
        print("  'vinkki' tai 'tip' - Saa satunnaisen yleisen vinkin")
        print("  'kaikki_vihjeet' - Näytä kaikki pelivihjeet")
        print("  'kaikki_vinkit' - Näytä kaikki yleiset vinkit")
        print("  'lopeta' tai 'quit' - Poistu")
        print()

        while True:
            try:
                command = input("TennisBot> ").strip().lower()
                
                if command in ['lopeta', 'quit', 'exit']:
                    print("Näkemiin! 🎾")
                    break
                elif command in ['vihje', 'hint']:
                    print(f"🎯 {self.get_random_hint()}")
                elif command in ['vinkki', 'tip']:
                    print(f"💡 {self.get_random_tip()}")
                elif command == 'kaikki_vihjeet':
                    print("🎯 Kaikki pelivihjeet:")
                    for i, hint in enumerate(self.get_all_hints(), 1):
                        print(f"  {i}. {hint}")
                elif command == 'kaikki_vinkit':
                    print("💡 Kaikki yleiset vinkit:")
                    for i, tip in enumerate(self.get_all_tips(), 1):
                        print(f"  {i}. {tip}")
                elif command in ['help', 'ohje']:
                    print("Käytettävissä olevat komennot:")
                    print("  vihje/hint - Satunnainen pelivihje")
                    print("  vinkki/tip - Satunnainen yleinen vinkki") 
                    print("  kaikki_vihjeet - Kaikki pelivihjeet")
                    print("  kaikki_vinkit - Kaikki yleiset vinkit")
                    print("  lopeta/quit - Poistu")
                else:
                    print("Tuntematon komento. Kirjoita 'ohje' saadaksesi ohjeita.")
                    
            except KeyboardInterrupt:
                print("\nNäkemiin! 🎾")
                break
            except EOFError:
                print("\nNäkemiin! 🎾")
                break

def main():
    """Pääfunktio"""
    bot = TennisBot()
    
    # Jos annetaan komentoriviargumentti, käytä sitä
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command in ['vihje', 'hint']:
            print(bot.get_random_hint())
        elif command in ['vinkki', 'tip']:
            print(bot.get_random_tip())
        elif command == 'kaikki_vihjeet':
            for hint in bot.get_all_hints():
                print(f"• {hint}")
        elif command == 'kaikki_vinkit':
            for tip in bot.get_all_tips():
                print(f"• {tip}")
        else:
            print("Tuntematon komento. Käytä: vihje, vinkki, kaikki_vihjeet, tai kaikki_vinkit")
    else:
        # Interaktiivinen tila
        bot.run_interactive()

if __name__ == "__main__":
    main()