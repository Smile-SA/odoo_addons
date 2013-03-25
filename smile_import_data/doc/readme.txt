Fonctionalité:
Description :
Dans le cadre d'une reprise des données, le module permet de:
	- Gestion des Runs d'import.
	- Génération automatique des templates à remplir pour chaque objet qu'on souhaite importer:
		Chaque template template inclut :
			Tous les champs à renseigner (hors many2many et one2many)
			Le libellé de chaque champ
			La description et le format attendu pour chaque champ
	- Vérifier la validité des données à importer avant de les injecter
	- Injecter les données via l'import classique d'OpenERP ou via un script.

Toutes ces fonctionalit�s sont accessibles depuis une interface graphique propos�e par le module.

I) Gestion des Runs:
I-1) Les Runs
	Chaque Run définit une reprise des données avec une version de fichier de données à un instant T.
	Un Run est initialisé depuis un Modéle de Run.
	
I-1-1) Description:
	Chaque Run liste l'ensemble des objets à importer :
	Chaque objet définit :
		- les fichiers de données associés. (Voir l'arborescence des Runs)
		- Les champs composants le fichier à vérifier et leurs descriptions.

	Chaque Run doit être initialisé depuis un Modéle de RUN afin de l'initialiser avec la liste des objets à importer.

	Les runs suivent un workflow:
		Brouillon: Pour la définition d'un Run.
		En cours: Représente l'état démarré d'un Run. Il n'est pas permis d'avoir plusieurs Runs à l'état "En cours" pour le même template.
		Clos: L'état terminé d'un Run
		
	Les fichiers de données sont au format .csv pour le moment et représente :
		Une photo d'une base de données d'un outil source à un instant T
		Un delta d'une base de données à l'instant T+1
		Ou des données saisies manuellement.
	
I-1-2) Fonctionalités proposées:
	- Initialisation d'un Run depuis un template de Run
	- Validation des données à importer
	- Injecter les données
	- Ouvrir/Clore un Run

I-2) Modéles de RUN
I-2-1) description
	Un modéle de Run est un RUN générique permettant d'initialiser d'autres RUN.
	Comme les Runs, on peut d�finir la liste des objets.
	Le templates de RUN permettent:
		D'initialiser automatiquement l'ensemble des champs (hors many2many et one2many) � renseigner pour chaque objet
		D'initialiser automatiquement l'ensemble des fichiers � charger pour chaque objet
		De g�n�rer l'ensemble des templates � transmettre au client.
		De sauvegarder un Template de RUN au format .yml pour pouvoir le r�cup�rer sur une autre base.
		
	Il reste � la charge de l'utilisateur de poffiner le r�glage de chaque objet:
		Supprimer/Modifier certains champs inutiles
		Rendre certains champ obligatoire au niveau des fichiers
		Changer le nom du fichier data
		Ajouter des scripts de validations
		Ajouter des scripts d'import.

I-2-2) Arborescnce d'un RUN:
Le dossier racine étant Runs/

Pour un modéle de RUN (#ModéleDeRun) l'arborescence du dossier est définie comme suit:

Runs/#ModéleDeRun	/Config/config_2013_03_12.yml
					/Templates/	res.partner.csv
								res.partner.adress.csv
					/Runs/	#Mod�leDeRun_2013_03_12/data/res.partner.csv
														res.partner.adress.csv
													/scripts/
													/..
											
							#Mod�leDeRun_2013_02_12/#Mod�leDeRun_2013_03_12/data/res.partner.csv
													res.partner.adress.csv
													/scripts/
													/..
													
III) Validation des données:
Une fois un Run est démarré il est possible d'effectuer les controles suivant sur chaque fichier:
	- Vérification des doublons (en se basant sur les clés définies pour chaque élément d'un fichier)
	- Vérification du format des clés
	- Vérification du fomat de chaque donn�es en fonction du type attendu
	- RAF: Vérification de l'existence des clés référencées dans le jeux de données

Les erreurs sont gérées sous format de logs.



Amélioraiton:

Initialisation des champs à valider: Prendre en compte yc les champs des objets hérités
Créer un modèle de template depuis un assistant
Dans l'initialisation des champs à valider traiter les champs related
Dans le cas d'un many2one au lieu de faire systématiquement référence à un .csv ajouter un champ text pour d�finir la liste des valeur attendues.
Ajouter lors de la validation des many2one bypasser les colonnes ne se terminant pas par /id

