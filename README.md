# No-Cloud Tuya v2

Intégration Home Assistant pour appareils Tuya **100% locale** — ajout simplifié par **QR Code**.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

---

## ✨ Nouveauté v2 — Ajout par QR Code

Plus besoin de saisir manuellement Device ID et Local Key !  
Le nouveau flux guide en **5 étapes automatiques** :

```
1. Saisir Client ID + Secret (iot.tuya.com)
        ↓
2. Un QR Code s'affiche dans Home Assistant
        ↓
3. Scanner avec l'app Smart Life / Tuya Smart
        ↓
4. Choisir l'appareil dans la liste (auto-détectée)
        ↓
5. Confirmer le nom et l'IP — c'est tout ✅
```

---

## Prérequis

1. Un compte sur [iot.tuya.com](https://iot.tuya.com) (gratuit)
2. Créer un projet Cloud → récupérer **Access ID** et **Access Secret**
3. L'app **Smart Life** ou **Tuya Smart** installée sur votre téléphone

> La connexion cloud n'est nécessaire **qu'une seule fois** pour la configuration.  
> Après setup, tout fonctionne **100% en local** sans internet.

---

## Installation via HACS

1. HACS → Intégrations → ⋮ → **Dépôts personnalisés**
2. URL : `https://github.com/jclycris/no-cloud_tuya` — Catégorie : **Integration**
3. Installez **No-Cloud Tuya** et redémarrez HA
4. **Paramètres → Appareils & Services → + Ajouter → No-Cloud Tuya**

---

## Fonctionnalités

- ✅ Ajout par QR Code (sans saisie manuelle)
- ✅ Détection automatique des appareils et Local Keys
- ✅ Scan réseau local pour trouver les IPs
- ✅ Communication **100% locale** après setup
- ✅ Protocoles 3.1, 3.3, 3.4, 3.5
- ✅ Intervalle de polling configurable (5–300s)

---

## Licence

MIT License
