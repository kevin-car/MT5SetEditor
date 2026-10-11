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

## Générer un installateur Windows (setup.exe)

Un installateur classique (installation dans `Program Files`, raccourcis
Menu Démarrer / Bureau, entrée dans "Applications et fonctionnalités",
désinstallation propre, association optionnelle des fichiers `.set`) peut
être généré avec [Inno Setup](https://jrsoftware.org/isinfo.php) (gratuit) :

1. Construire l'exécutable (`dist\MT5SetEditor.exe`, voir ci-dessus).
2. Installer Inno Setup : `winget install --id JRSoftware.InnoSetup -e`
3. Compiler le script `installer.iss` fourni :
   ```powershell
   & "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer.iss
   ```
4. L'installateur est généré dans `installer_output\MT5SetEditor_Setup.exe`.

Distribuez ce fichier unique : il installe l'application, crée les
raccourcis, et propose une case à cocher pour ouvrir les `.set` par
double-clic avec MT5 Set Editor.

## Listes de choix (comme dans le testeur MT5)

Un double-clic sur Valeur / Minimum / Maximum ouvre une liste déroulante pour :

- les booléens (`false` / `true`) ;
- les timeframes (`Current`, `1 Minute`, … `1 Month`) ;
- les heures (00:00 → 23:55 par pas de 5 min) ;
- les énumérations, détectées automatiquement (pas = `0` et bornes entières
  dans le `.set`).

Le `.set` ne contient que la valeur entière des énumérations : les libellés
affichés par MT5 viennent de l'EA compilé (`.ex5`, chiffré). Les libellés
des méthodes de moyenne mobile (`*_Method`) et de `Trade_Direction` sont
fournis. Pour les autres : **clic droit sur la ligne → Définir les
libellés…**, saisissez le texte de chaque valeur. Ils sont enregistrés
globalement (`~/.mt5_set_editor/enums.json`) et réutilisés pour tous les
fichiers. Le fichier `.set` conserve toujours les valeurs entières.

## Structure du projet

- `main.py` — point d'entrée de l'application.
- `main_window.py` — fenêtre principale (table des paramètres, filtres).
- `filter_dialog.py` — boîte de dialogue de création/édition d'un filtre.
- `set_parser.py` — lecture/écriture des fichiers `.set`.
- `filter_manager.py` — persistance des filtres (JSON).
- `enum_manager.py` / `enum_dialog.py` — libellés des énumérations.
- `sample.set` — fichier d'exemple pour tester l'application.
