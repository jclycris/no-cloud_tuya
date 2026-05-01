# No-Cloud Tuya

Intégration Home Assistant pour appareils Tuya **100% locale** — aucune connexion au cloud Tuya requise.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

---

## Fonctionnalités

- ✅ Communication **locale** via le protocole Tuya (tinytuya)
- ✅ Pas de compte Tuya Cloud nécessaire au runtime
- ✅ Support Switch / Prise connectée (DP1)
- ✅ Config Flow graphique (UI Home Assistant)
- ✅ Options flow (intervalle de rafraîchissement configurable)
- ✅ Compatibilité protocoles **3.1, 3.3, 3.4, 3.5**

---

## Prérequis

1. Connaître l'**adresse IP locale** de votre appareil Tuya
2. Connaître le **Device ID** et la **Local Key** de l'appareil

> **Comment obtenir la Local Key ?**
> Utilisez [tinytuya wizard](https://github.com/jasonacox/tinytuya#setup-wizard---getting-local-keys) ou l'outil [tuya-cli](https://github.com/TuyaAPI/cli). Vous aurez besoin d'un compte développeur Tuya IoT Platform (uniquement pour cette étape initiale).

---

## Installation via HACS

1. Dans HACS → **Intégrations** → Menu ⋮ → **Dépôts personnalisés**
2. Ajoutez l'URL de ce dépôt, catégorie : **Integration**
3. Recherchez **No-Cloud Tuya** et installez
4. Redémarrez Home Assistant
5. Allez dans **Paramètres → Appareils & Services → Ajouter une intégration**
6. Cherchez **No-Cloud Tuya** et suivez les étapes

---

## Installation manuelle

Copiez le dossier `custom_components/no_cloud_tuya/` dans votre répertoire `config/custom_components/` de Home Assistant.

---

## Configuration

| Champ | Description | Exemple |
|---|---|---|
| Nom | Nom affiché dans HA | `Prise salon` |
| Adresse IP | IP locale de l'appareil | `192.168.1.42` |
| Device ID | Identifiant unique Tuya | `eb...` |
| Local Key | Clé de chiffrement locale | `a1b2c3...` |
| Version protocole | Version du protocole Tuya | `3.3` |

---

## Dépannage

**L'appareil apparaît indisponible :**
- Vérifiez que l'IP est correcte et fixe (bail DHCP statique recommandé)
- Vérifiez que la Local Key n'a pas changé (elle change si vous réinitialisez l'appareil ou le re-pairez)

**Erreur "cannot_connect" au setup :**
- Assurez-vous que l'appareil est sur le même réseau local que Home Assistant
- Testez avec `tinytuya` en ligne de commande : `python -m tinytuya scan`

---

## Licence

MIT License — voir [LICENSE](LICENSE)
