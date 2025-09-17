# TennisBot 🎾

TennisBot on Python-pohjainen botti, joka tarjoaa tennisvihjeitä ja -vinkkejä. Botti vastaa kysymykseen "AJAAKO TÄMÄ BOTTI JO VALMIITA VIHJEITÄ" - kyllä, botti tarjoaa valmiita vihjeitä!

## Ominaisuudet

- 🎯 **Pelivihjeet**: Teknisiä neuvoja pelin parantamiseksi
- 💡 **Yleiset vinkit**: Hyödyllisiä neuvoja tennispelaajille
- 🔄 **Satunnaisuus**: Saat erilaisia vinkkejä joka kerta
- 🗣️ **Kaksikielisyys**: Toimii suomeksi ja englanniksi
- 💻 **Kaksi käyttötapaa**: Komentorivi ja interaktiivinen tila

## Asennus

1. Kloonaa repository:
```bash
git clone https://github.com/mxxx222/TennisBot.git
cd TennisBot
```

2. Varmista että Python 3 on asennettu:
```bash
python3 --version
```

## Käyttö

### Komentoriviargumentit

Voit käyttää bottia yksittäisillä komennoilla:

```bash
# Satunnainen pelivihje
python3 tennis_bot.py vihje
python3 tennis_bot.py hint

# Satunnainen yleinen vinkki
python3 tennis_bot.py vinkki  
python3 tennis_bot.py tip

# Kaikki pelivihjeet
python3 tennis_bot.py kaikki_vihjeet

# Kaikki yleiset vinkit
python3 tennis_bot.py kaikki_vinkit
```

### Interaktiivinen tila

Käynnistä interaktiivinen tila ilman argumentteja:

```bash
python3 tennis_bot.py
```

Interaktiivisessa tilassa voit käyttää seuraavia komentoja:
- `vihje` tai `hint` - Satunnainen pelivihje
- `vinkki` tai `tip` - Satunnainen yleinen vinkki
- `kaikki_vihjeet` - Näytä kaikki pelivihjeet
- `kaikki_vinkit` - Näytä kaikki yleiset vinkit
- `ohje` tai `help` - Näytä ohje
- `lopeta` tai `quit` - Poistu

## Esimerkkejä

### Pelivihjeet
```
🎯 Pidä mailasta tiukasti kiinni, mutta älä jännittele rannettas liikaa.
🎯 Katso palloa aina mailaniskuun asti.
🎯 Harjoittele palvelua säännöllisesti - se on tärkein isku.
```

### Yleiset vinkit
```
💡 Lämittele aina ennen peliä vammojen välttämiseksi.
💡 Juo vettä säännöllisesti pelin aikana.
💡 Tee venyttelyjä pelin jälkeen.
```

## Tekninen toteutus

- **Kieli**: Python 3
- **Riippuvuudet**: Vain Python:n standardikirjasto
- **Tiedostot**: 
  - `tennis_bot.py` - Pääohjelma
  - `requirements.txt` - Riippuvuudet (tyhjä)
  - `README.md` - Tämä dokumentaatio

## Vastaus kysymykseen

**"AJAAKO TÄMÄ BOTTI JO VALMIITA VIHJEITÄ?"**

✅ **KYLLÄ!** Tämä botti sisältää:
- 10 valmiiksi ohjelmoitua pelivihjettä
- 10 valmiiksi ohjelmoitua yleistä vinkkiä
- Toimivan käyttöliittymän vihjeiden saamiseksi
- Sekä satunnaisten että kaikkien vihjeiden näyttämisen

## Lisenssi

Avoimen lähdekoodin projekti.