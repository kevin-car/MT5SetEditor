# MT5 Set Editor

Éditeur de fichiers `.set` (paramètres d'Expert Advisor MetaTrader 5), avec
système de filtres personnalisés pour n'afficher que les paramètres qui
vous intéressent (ex: tous les champs liés au "Grid").

## Fonctionnalités

- Ouverture / édition / sauvegarde de fichiers `.set` en conservant la
  structure d'origine (commentaires, sections, ordre des lignes).
- Édition des colonnes **Valeur**, **Défaut**, **Min**, **Max** et de la
  case **Optimiser** (Y/N) pour les paramètres optimisables
  (`Nom=Valeur||Défaut||Min||Max||Y`).
- Création de **filtres** : sélectionnez une liste de noms de paramètres
  (ex: `Grid_Recovery_Factor`, `Grid_Lot_Sum`, `Grid_Special_Reaction`) et
  donnez un nom au filtre (ex: "Grid"). Cliquez sur ce filtre dans le
  panneau de gauche pour n'afficher que ces paramètres dans le tableau.
- Les filtres sont enregistrés globalement (`~/.mt5_set_editor/filters.json`)
  et restent disponibles pour tous les fichiers `.set` ouverts par la suite.
- Barre de recherche pour filtrer rapidement par nom de paramètre.

## Installation

```powershell
pip install -r requirements.txt
```

## Lancement

```powershell
python main.py
```

Un fichier d'exemple `sample.set` est fourni pour tester l'application.

## Créer un filtre "Grid"

1. Ouvrez un fichier `.set`.
2. Cliquez sur **Nouveau** dans le panneau de gauche.
3. Donnez le nom `Grid`, cochez les paramètres voulus (ex: tous ceux
   commençant par `Grid_`), utilisez la recherche pour les trouver
   rapidement.
4. Validez : le filtre apparaît dans la liste. Cliquez dessus pour
   n'afficher que ces paramètres dans le tableau.

## Générer un exécutable Windows (.exe)

```powershell
pip install pyinstaller
pyinstaller --noconsole --onefile --name "MT5SetEditor" main.py
```

L'exécutable sera généré dans le dossier `dist/`.

## Structure du projet

- `main.py` — point d'entrée de l'application.
- `main_window.py` — fenêtre principale (table des paramètres, filtres).
- `filter_dialog.py` — boîte de dialogue de création/édition d'un filtre.
- `set_parser.py` — lecture/écriture des fichiers `.set`.
- `filter_manager.py` — persistance des filtres (JSON).
- `sample.set` — fichier d'exemple pour tester l'application.
