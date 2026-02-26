# 📈 Technical Analyst

Une application web moderne d'analyse technique financière en temps réel, construite avec Flask et alimentée par des données de marché en direct.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Fonctionnalités

### 📊 Analyse Technique Avancée
- **Graphiques interactifs multi-panneaux** avec Plotly.js
  - Chandelier japonais (candlestick) avec contrôles de période (1M, 3M, 6M, 1A, 2A)
  - Volume avec code couleur
  - RSI (14) avec zones de surachat/survente
  - MACD (12, 26, 9) avec histogramme
- **Indicateurs techniques configurables**
  - Moyennes mobiles (MA20, MA50, MA200)
  - Bandes de Bollinger
  - Ligne de prix continue
  - Toggle instantané des indicateurs

### 🔍 Recherche Intelligente
- Recherche en temps réel par ticker ou nom d'entreprise
- Dropdown avec suggestions enrichies (badge marché US/EU)
- Intégration Yahoo Finance pour recherche étendue
- Actions populaires en accès rapide

### 💼 Gestion de Portefeuille
- Ajout/suppression d'actions avec stockage localStorage
- Onglets de filtrage (Toutes, US, EU)
- Données en temps réel avec refresh automatique (30s)
- Bouton d'ajout contextuel depuis la page d'analyse
- État visuel du portefeuille (badge vert si ajouté)

### 🎯 Indicateurs Financiers
- RSI, MACD, moyennes mobiles calculées côté serveur
- Volatilité, Beta, P/E Ratio
- Plus haut/bas 52 semaines
- Rendement dividende
- Tableau de données historiques

### 🎨 Interface Moderne
- Design dark mode avec thème personnalisable
- Ticker de marché avec défilement infini fluide
- Navigation responsive avec menu mobile
- Animations et transitions soignées
- Composants réutilisables

## 🚀 Installation

### Prérequis
- Python 3.8+
- pip
- Git



## 📦 Dépendances Principales

```
flask==3.0.0
yfinance==0.2.32
pandas==2.1.3
numpy==1.26.2
plotly==5.18.0
requests==2.31.0
flask-caching==2.1.0
```

## 🏗️ Architecture

```
technical-analyst/
├── app.py                      # Application Flask principale
├── modules/
│   └── data_fetcher.py         # Module de récupération de données (Yahoo Finance)
├── templates/
│   ├── index.html              # Page d'accueil
│   ├── analyse.html            # Page d'analyse avec graphiques
│   ├── portefeuille.html       # Gestion du portefeuille
│   ├── dashboard.html          # Tableau de bord système
│   └── components/
│       ├── navbar.html         # Barre de navigation avec ticker
│       ├── footer.html         # Pied de page
│       └── search_bar.html     # Barre de recherche avec dropdown
├── static/
│   ├── css/
│   │   ├── main.css            # Styles globaux
│   │   ├── navbar.css          # Styles de navigation
│   │   ├── search_bar.css      # Styles de recherche
│   │   └── analyse.css         # Styles de la page d'analyse
│   └── js/
│       └── main.js             # Scripts JavaScript globaux
└── requirements.txt
```

## 🎨 Composants Clés

### Système de Graphiques
- **Backend** : Calculs d'indicateurs avec NumPy (RSI, MACD, Bollinger Bands)
- **Frontend** : Visualisation interactive avec Plotly.js
- **Performance** : Calculs vectorisés, cache Flask avec TTL 5min

### Recherche
- **API** : `/api/search?q=<query>` - Recherche multi-source (local + Yahoo Finance)
- **Debounce** : 260ms pour éviter les requêtes excessives
- **Dropdown** : Rendu dynamique avec `position:fixed` et repositionnement RAF

### Portefeuille
- **Stockage** : `localStorage` côté client avec structure `{ticker, market}`
- **Synchronisation** : Vérification au chargement de chaque page d'analyse
- **API** : `/api/quote/<ticker>` pour données temps réel


## 📡 API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Page d'accueil |
| `/analyse` | GET | Page d'analyse (paramètre `?ticker=AAPL`) |
| `/portefeuille` | GET | Gestion du portefeuille |
| `/dashboard` | GET | Tableau de bord système |
| `/api/search` | GET | Recherche d'actions (`?q=apple`) |
| `/api/quote/<ticker>` | GET | Citation temps réel |
| `/api/clear-cache` | POST | Vider le cache |

## 🎯 Roadmap

- [ ] Authentification utilisateur
- [ ] Sauvegarde du portefeuille côté serveur
- [ ] Alertes de prix personnalisées
- [ ] Export PDF des analyses
- [ ] Comparaison multi-actions
- [ ] Backtesting de stratégies
- [ ] API REST complète



## 📝 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👤 Auteur

STELNICEANU Guillaume 





