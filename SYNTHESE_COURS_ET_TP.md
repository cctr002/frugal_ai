# IA frugale : synthèse du cours et guide détaillé des TP

**Cours :** *Frugal AI: Rethinking model design and objective for a sustainable future*.
**Enseignants :** David Cornu et Aristide Doussot. PSL Week 2026, accueillie à l'ESPCI.
**Source principale :** [support PDF local](frugal_ai.pdf), 52 pages. Rédaction le 23 novembre 2026.

Ce document suit tout le contenu disponible dans le PDF, y compris ses graphiques et schémas. Les références « p. » désignent les pages du fichier. Les pieds de page annoncent « / 100 », mais la version présente dans le dépôt s'arrête à la page 52.

La première partie synthétise le cours. La seconde transforme les objectifs du premier TP en une procédure de travail détaillée. **Le dépôt ne contient, à la date de lecture, que le PDF et un README sommaire : aucun énoncé séparé, code de départ ou jeu de données n'est fourni localement.** Les étapes pratiques proposées ci-dessous complètent donc les objectifs de la page 52 ; elles ne constituent pas un énoncé officiel supplémentaire. Le second TP est annoncé, mais pas développé dans ce support.

## Sommaire

- [I. Synthèse exhaustive du cours](#cours)
- [II. Guide précis du TP 1 : multiplication de matrices](#tp1)
- [III. TP 2 : ce qui est annoncé et comment le préparer](#tp2)
- [IV. Correspondance avec les 52 pages du support](#correspondance)
- [V. Glossaire](#glossaire)

<a id="cours"></a>

## I. Synthèse exhaustive du cours

### 1. Objectif et organisation de la semaine — p. 1-3 et 19

L'objectif est de comprendre comment le fonctionnement réel des ordinateurs et la conception des programmes influencent leur consommation énergétique, puis d'utiliser cette compréhension pour concevoir une IA plus économe.

L'IA frugale suppose deux décisions complémentaires : déterminer le service réellement nécessaire et son budget de ressources ; optimiser ensuite les moyens techniques permettant de le rendre.

Le programme provisoire est le suivant :

| Période | Contenu annoncé |
| --- | --- |
| Jour 1 | Impacts environnementaux du numérique ; première multiplication matricielle naïve en Python. |
| Jours 2-3 | Passage au C compilé ; optimisations progressives jusqu'au fonctionnement bas niveau. |
| Jour 3 | Parallélisation CPU en C ; introduction à la multiplication matricielle sur GPU. |
| Jour 4 | Architecture des réseaux de neurones et coût des calculs. |
| Jours 4-5 | Classification d'images sous budget énergétique imposé. |

La validation annoncée repose sur **la présence pendant toute la semaine et un rapport de travaux pratiques**. Le PDF ne fixe ni longueur du rapport, ni date de remise, ni barème détaillé.

Le support indique que diapositives, exercices, codes, corrections et données sont destinés à être publiés progressivement dans le dépôt pédagogique `Deyht/frugal_ai`. Il recommande de travailler dans un répertoire personnel ou sur un support externe : le dossier de téléchargement des ordinateurs de la salle est effacé quotidiennement.

### 2. Pourquoi partir de l'impact du numérique ? — p. 4-8

Le graphique introductif du GIEC oppose les trajectoires d'émissions associées aux politiques mises en œuvre à celles permettant de limiter le réchauffement à 1,5 °C ou 2 °C. Il situe l'efficacité informatique dans un besoin général de réduction des émissions.

Un modèle d'IA est un programme qui produit une réponse à partir de données. Sa particularité est d'apprendre certaines règles par des méthodes statistiques, mais il utilise les mêmes infrastructures physiques que les autres logiciels. Pour comprendre son impact, il faut donc considérer l'ensemble des **TIC**, technologies de l'information et de la communication, ou **ICT** dans le support.

Le cours cite environ **4 % des émissions mondiales de gaz à effet de serre** pour les TIC, et une évolution de **2,5 % en 2020 à 4,4 % en 2024 en France**. Ce sont les chiffres et références présentés dans les diapositives, pas une actualisation indépendante. Le cours souligne surtout la croissance du secteur, notamment liée à l'IA et aux objets connectés.

Trois ensembles contribuent à l'impact :

| Ensemble | Exemples | Ce qu'il faut comptabiliser |
| --- | --- | --- |
| Terminaux | Ordinateurs, téléphones, objets connectés. | Fabrication, renouvellement, usage et fin de vie. |
| Réseaux | Routeurs, antennes, câbles et équipements de transmission. | Infrastructure physique, fonctionnement et échanges de données. |
| Centres de données | Serveurs, stockage et services centralisés. | Calculs, stockage, alimentation, refroidissement et fabrication. |

La page 8 compare trois estimations de la répartition de l'empreinte carbone des TIC, hors télévision :

| Estimation reproduite | Terminaux | Centres de données | Réseaux |
| --- | ---: | ---: | ---: |
| Andrae et Edler, scénario 2020 « best case » | 32 % | 33 % | 35 % |
| Belkhir et Elmeligi, scénario moyen 2020 | 37 % | 41 % | 22 % |
| Malmodin, estimation 2020 | 57 % | 18 % | 24 % |

Les arrondis peuvent empêcher la somme de faire exactement 100 %. La légende donne aussi des totaux différents : 623, 1 207 et 690 MtCO₂e respectivement. **Le titre de la diapositive parle d'énergie, mais ces diagrammes sont légendés comme des répartitions de l'empreinte carbone.** Ces différences illustrent la sensibilité des résultats aux hypothèses : durée de vie, origine de l'électricité, conditions de fabrication, provenance des matériaux et périmètre retenu. Par exemple, faut-il rattacher l'ordinateur d'une voiture autonome au numérique ou à la mobilité ?

### 3. Le cycle de vie et la matérialité des équipements — p. 9-13

L'impact d'un équipement se distribue sur plusieurs étapes :

1. Extraction et transformation des matières premières.
2. Fabrication des composants et assemblage.
3. Transport et distribution.
4. Utilisation.
5. Fin de vie, traitement des déchets et éventuelle valorisation.

Le cours insiste sur le fait que **l'utilisation n'est qu'une partie du bilan**. Dans l'exemple ADEME reproduit, la fabrication d'un ordinateur de 2 kg mobilise 600 kg de matières premières et génère 103 kg de CO₂, sur 156 kg sur l'ensemble de son cycle de vie. Il s'agit d'un exemple du support, pas d'une valeur applicable à tout ordinateur.

Conséquence : prolonger la durée de vie d'un équipement peut être plus bénéfique que le remplacer par une version consommant moins à l'usage. Le gain opérationnel du remplacement doit compenser l'impact de fabrication du nouvel appareil. L'obsolescence et les renouvellements prématurés vont à l'encontre de cette logique.

La chaîne de production est mondiale. Conception, extraction, fabrication, assemblage, utilisation et recyclage peuvent se dérouler dans des pays différents. De même, un service accessible instantanément peut dépendre d'un serveur physiquement très éloigné.

La carte de la page 10 illustre les différences d'intensité carbone de l'électricité entre pays. Un même calcul peut donc avoir une empreinte carbone différente selon son lieu d'exécution. La durée nécessaire pour que les économies d'usage compensent la fabrication dépend aussi de ce contexte.

Les exemples du smartphone montrent :

- Une chaîne d'approvisionnement internationale avec de nombreux transports.
- Une forte diversité de matériaux : verre, céramiques, plastiques, métaux courants, précieux et terres rares.
- Des éléments différents dans l'écran, la batterie, les circuits et le boîtier : par exemple indium, silicium, cuivre, lithium et cobalt.
- Une production de masse qui amplifie les conséquences de chaque choix de conception et de renouvellement.

Le seul CO₂ équivalent ne suffit pas à décrire tous les dommages. L'analyse de cycle de vie reproduite page 13 distingue notamment réchauffement climatique, acidification, eutrophisation, atteinte à la couche d'ozone, toxicité humaine, écotoxicité, demande d'énergie primaire, consommation d'eau et déchets. L'importance des différentes étapes du cycle de vie varie selon l'indicateur. Réduire un impact ne signifie donc pas nécessairement les réduire tous.

### 4. IA, GPU, croissance des infrastructures et choix collectifs — p. 14-18

Les GPU permettent d'exécuter efficacement de nombreux calculs parallèles utilisés en apprentissage automatique. Le support replace leur développement dans l'histoire du jeu vidéo, du calcul scientifique, du calcul généraliste sur GPU, du minage de cryptomonnaies puis de l'essor de l'IA générative.

Le graphique économique sur NVIDIA sert à illustrer les investissements et variations de demande. L'enjeu pédagogique est que la diffusion de l'IA dépend aussi des capacités industrielles, des investissements et de la disponibilité des puces ; elle ne se résume pas aux algorithmes.

Les pages 15-17, fondées sur des extraits du Shift Project, décrivent une boucle :

> Davantage d'usages augmente la demande de capacité ; davantage de capacité rend possibles de nouveaux usages.

L'intégration de l'IA dans les services, l'augmentation du nombre d'utilisateurs et l'intensification des usages individuels peuvent ainsi alimenter la construction de nouvelles infrastructures.

Les projections reproduites page 16 présentent une trajectoire sectorielle incompatible avec une forte réduction des émissions : environ +9 % d'émissions par an dans le scénario montré, comparé à une diminution de 5 % par an indiquée comme nécessaire pour l'objectif considéré. Elles évoquent aussi un doublement possible de l'électricité consommée par les centres de données européens entre 2023 et 2030, puis un quadruplement entre 2023 et 2035, ainsi qu'une forte part des centres de données dans l'électricité irlandaise. **Ce sont les scénarios et constats rapportés par le support, pas des prévisions recalculées ici.**

Le message est que décarboner l'électricité et réduire l'empreinte de fabrication ne suffisent pas si le volume d'activité croît trop vite. Le support appelle à encadrer la consommation totale et à expliciter les choix de déploiement.

La démarche proposée est :

1. Définir le besoin et le budget énergétique ou carbone.
2. Optimiser le modèle et le matériel.
3. Revoir les fonctionnalités, jusqu'à en transformer ou supprimer certaines.
4. Adapter l'ampleur du déploiement au besoin : usage ciblé ou généralisation.
5. Si le budget reste incompatible, abandonner la solution ou recourir à une solution sans IA.

Quatre leviers collectifs sont présentés : mesure et transparence ; optimisation ; sobriété et trajectoire de consommation plafonnée ; connaissances, formation et compétences.

La page 18 signale plusieurs questions laissées ouvertes : contribution éventuelle du numérique aux autres transitions, croissance des débits, limites des liaisons intercontinentales, dépendances géopolitiques, continuité des réseaux, déchets électroniques, recyclage et régulation des usages. Elle mentionne EcoInfo, communauté de recherche du CNRS, comme ressource sur ces enjeux.

### 5. Du programme au matériel — p. 20-24

Le cours recentre ensuite l'analyse sur l'efficacité du calcul. Le schéma simplifié est :

```text
Code de haut niveau -> instructions de plus bas niveau -> code machine exécuté par le CPU
```

Les architectures peuvent prendre des formes très différentes : portable, station de travail, serveur, smartphone ou micro-ordinateur. Elles partagent néanmoins des fonctions fondamentales :

| Composant | Rôle |
| --- | --- |
| CPU | Exécuter les instructions et effectuer les calculs. |
| RAM | Conserver les données et instructions en mémoire de travail. |
| Stockage | Conserver durablement programmes et données. |
| Carte mère et interconnexions | Relier les composants et les périphériques. |
| GPU éventuel | Accélérer certains calculs, notamment parallèles. |
| Alimentation et refroidissement | Fournir l'énergie électrique et évacuer la chaleur. |

Un CPU est un circuit électronique constitué de très nombreux transistors. Il exécute des instructions arithmétiques, logiques et d'entrée-sortie. Un processeur moderne intègre plusieurs cœurs, des caches et des interfaces. La photographie annotée page 24 rappelle que toute la surface d'une puce n'est pas dédiée au calcul : caches, contrôleurs mémoire, entrées-sorties et parfois circuit graphique occupent également de la place.

### 6. Les déterminants des performances d'un CPU — p. 25-27

Trois paramètres structurent la présentation :

- **IPC, instructions par cycle** : quantité de travail en instructions accomplie par cycle, qui dépend notamment du pipeline, des dépendances et de la mémoire.
- **Fréquence** : nombre de cycles par seconde.
- **Nombre de cœurs** : possibilité d'exécuter plusieurs flux de travail en parallèle.

À travail en instructions comparable, le produit IPC × fréquence donne une intuition du débit d'un cœur ; il ne suffit pas à comparer tous les programmes ou toutes les architectures. Une instruction peut elle-même traiter plusieurs données.

La fréquence est limitée par la consommation et la chaleur. Les mécanismes de variation dynamique et de « boost » permettent une fréquence élevée pendant une courte charge. En charge prolongée, l'échauffement et les capacités du refroidissement peuvent conduire à une fréquence stabilisée plus faible.

Une mesure de quelques secondes sur une machine froide peut donc présenter de meilleures performances qu'un calcul prolongé. Utiliser tous les cœurs peut aussi diminuer leur fréquence individuelle.

Le multithreading matériel, dont Hyper-Threading est un exemple, permet à plusieurs fils logiques d'utiliser un même cœur physique. Il peut améliorer l'utilisation des unités d'exécution, mais n'équivaut pas à ajouter autant de cœurs physiques. Les gains dépendent du travail exécuté et des ressources partagées.

Le graphique historique page 26 montre que le nombre de transistors et de cœurs a continué de croître, alors que la fréquence ne progresse plus au même rythme. Les gains passent davantage par l'architecture, le parallélisme et la spécialisation. La loi de Moore concerne la croissance de l'intégration des transistors ; elle ne garantit pas un doublement automatique de la vitesse de tout programme.

La fabrication se fait par lots sur des plaques de silicium, les *wafers*, par photolithographie. Des puces plus grandes et des procédés plus fins peuvent rendre la production plus difficile et augmenter le coût des défauts. Deux exemplaires d'un même modèle ne sont pas parfaitement identiques : c'est la variabilité de fabrication, parfois appelée *silicon lottery*. Le cours cite quelques pourcents de variation à l'échelle d'un composant et jusqu'à 10 % à l'échelle d'une installation en cumulant les sources de variabilité.

### 7. Puissance, durée et énergie : bien mesurer — p. 28-30

**La puissance est un débit d'énergie ; l'énergie est la quantité consommée sur une durée.**

| Grandeur | Unité | Sens |
| --- | --- | --- |
| Puissance P | Watt, W | Joules consommés par seconde. |
| Durée T | Seconde, s | Temps de l'opération. |
| Énergie E | Joule, J | Puissance intégrée sur la durée. |

Pour une puissance approximativement constante :

```text
E = P × T
1 J = 1 W × 1 s
1 Wh = 3 600 J
1 kWh = 3 600 000 J
```

Une machine a une consommation de base, même sans travail utile : RAM, périphériques, composants prêts à répondre, système d'exploitation, etc. Un serveur réel ne se comporte donc pas comme une machine idéale dont la consommation serait strictement proportionnelle à l'activité. Un équipement arrêté peut également avoir une consommation résiduelle, généralement bien plus faible.

Deux périmètres de mesure répondent à deux questions différentes :

```text
Énergie totale pendant le calcul : E_total = intégrale de P_charge(t) sur la durée T
Énergie supplémentaire : E_dyn = intégrale de [P_charge(t) - P_repos(t)] sur T
```

Si la référence au repos est constante et la puissance supplémentaire assez stable, la formule de la page 29 devient :

```text
E_dyn ≈ ΔP × T, avec ΔP = P_charge - P_repos
```

Soustraire le repos permet de comparer certains coûts supplémentaires. Pour un bilan complet d'utilisation d'une infrastructure, la consommation de base doit être attribuée aux usages : elle ne disparaît pas parce qu'on la soustrait dans un benchmark.

**Exemple pédagogique, ajouté pour comprendre le calcul :** un programme à 100 W pendant 10 s consomme 1 000 J ; un autre à 70 W pendant 20 s consomme 1 400 J. Le second a une puissance plus faible, mais consomme davantage d'énergie.

Avant de mesurer, le cours demande de choisir un état thermique :

- **À froid** : pertinent pour certaines opérations ponctuelles courtes, mais peu représentatif d'une activité soutenue.
- **À chaud** : machine préalablement mise en charge jusqu'à un régime stable ; état de référence privilégié pour un calcul prolongé, avec un coût de préparation supplémentaire.

Il faut distinguer cet état thermique du fait que les caches contiennent déjà ou non les données.

Enfin, **100 % d'utilisation CPU n'implique pas une puissance identique pour tous les programmes**. La page 30 montre environ 17 % d'écart dans l'exemple présenté, malgré une utilisation complète des serveurs. Les instructions exécutées et les accès mémoire modifient la puissance réelle.

### 8. Fréquence, puissance et efficacité : chercher un optimum — p. 31-33

Augmenter la fréquence tend à augmenter la puissance et à réduire le temps d'exécution. Le produit des deux n'évolue pas nécessairement de manière monotone : une fréquence intermédiaire peut minimiser l'énergie.

Inversement, ralentir fortement un calcul peut prolonger suffisamment la consommation de base pour annuler les gains de puissance. Il faut mesurer l'énergie de la tâche complète.

Les exemples comparent des Xeon E5-2630 et E5-2630L. Ils montrent que la désignation « low power » décrit une caractéristique de puissance, mais ne suffit pas à conclure sur les joules consommés pour une tâche. La position du meilleur point dépend du programme et du matériel.

Limiter la puissance ou la fréquence maximale peut améliorer l'efficacité de certains systèmes. Le support évoque également l'abaissement de tension lorsque la stabilité le permet. Ces pistes ne donnent pas un réglage universel.

Le cours présente enfin un compromis entre efficacité, performance et coût : puces haut de gamme, matériel d'entrée de gamme, processeurs de portables, objets connectés et serveurs répondent à des priorités différentes. La fiabilité et le coût d'exploitation comptent particulièrement pour les serveurs. Ces tendances servent à raisonner sur le choix du matériel, pas à classer systématiquement chaque famille.

### 9. Passer à plusieurs processeurs ou plusieurs machines — p. 34-38

Deux grandes organisations permettent d'augmenter les ressources :

| Organisation | Principe | Coûts et limites |
| --- | --- | --- |
| Mémoire partagée | Plusieurs cœurs ou processeurs accèdent à une mémoire commune. | Concurrence sur les accès, synchronisation, bande passante partagée et coût du matériel. |
| Mémoire distribuée | Plusieurs machines disposent chacune de leur mémoire et échangent sur un réseau. | Transferts, latence, synchronisation, réseau et infrastructure supplémentaires. |

Multiplier les ressources n'assure pas un gain proportionnel. Il faut disposer de travail parallélisable et limiter les échanges ainsi que les attentes.

Un centre de données consomme au-delà de ses seules unités de calcul. Le schéma page 35 représente alimentation, transformateurs, batteries, groupes de secours, sécurité, réseaux et refroidissement. Le périmètre de mesure doit préciser lesquels sont inclus.

Le cours oppose le fonctionnement recherché des clusters scientifiques, avec une forte occupation, au dimensionnement des infrastructures cloud et réseau sur la charge maximale prévue. La consommation de base d'une capacité souvent sous-utilisée représente une dépense importante. Le graphique de trafic illustre de fortes variations de demande au cours du temps.

Les pages 37-38 comparent des instantanés de classements **TOP500**, centrés sur la performance de calcul, et **Green500**, centrés sur la performance par unité de puissance. L'enseignement est que le système le plus rapide n'est pas nécessairement le plus efficace énergétiquement. Les classements reproduits sont des exemples du support, pas des classements actuels vérifiés.

### 10. Les leviers d'amélioration à plusieurs échelles — p. 39

| Échelle | Pistes du cours |
| --- | --- |
| Processeur | Améliorer l'IPC, choisir un fonctionnement efficace et recourir à des accélérateurs spécialisés. |
| Machine | Exploiter les cœurs, placer correctement les données et limiter les déplacements inutiles. |
| Groupe de machines | Améliorer les communications, la répartition du travail et le traitement des goulots d'étranglement. |
| Centre de données | Lisser la charge, adapter les ressources actives à la demande et arrêter des parties inutilisées lorsque c'est possible. |

Les FPGA, GPU et NPU sont cités comme accélérateurs possibles. Leur intérêt dépend de l'adéquation entre le travail à effectuer et leur architecture.

Optimiser uniquement les centres de données ne suffit pas : terminaux, réseaux, fabrication et croissance des usages restent dans le bilan global.

### 11. L'effet rebond — p. 40

Le paradoxe de Jevons désigne ici un mécanisme possible :

```text
Meilleure efficacité -> coût unitaire plus faible -> davantage d'usages -> consommation globale accrue
```

Une optimisation peut diminuer le coût d'une requête tout en encourageant une multiplication des requêtes, des utilisateurs ou des fonctionnalités. Les économies obtenues peuvent aussi être dépensées dans d'autres activités polluantes : c'est un autre mécanisme de rebond économique.

Le cours souligne que les gains sont plus directement bénéfiques lorsque le volume du service rendu reste stable. Pour évaluer une amélioration, il faut donc distinguer **l'efficacité par opération** de **la consommation totale**.

### 12. Pourquoi optimiser les programmes ? — p. 41-43

Les exemples historiques de cartes perforées et de machines disposant de très peu de mémoire illustrent une époque où la rareté des ressources imposait une grande attention à l'implémentation.

Les priorités actuelles incluent souvent le temps de développement, la facilité d'utilisation et de déploiement, la sécurité, la continuité du service et la mutualisation. Les langages de haut niveau, conteneurs et machines virtuelles participent à ces objectifs, mais leurs couches d'abstraction peuvent ajouter des coûts.

Le support oppose de façon pédagogique :

- Les **langages compilés**, qui permettent au compilateur d'analyser et d'optimiser le programme et offrent un contrôle plus direct des données et de la mémoire.
- Les **langages interprétés**, qui facilitent de nombreuses tâches de programmation, avec un coût possible pour l'exécution directe d'opérations élémentaires et moins de visibilité sur certains mécanismes matériels.

Il faut comprendre cette distinction comme une tendance d'implémentation. Des environnements interprétés peuvent utiliser de la compilation JIT, et un programme Python peut déléguer l'essentiel de ses calculs à des bibliothèques natives compilées. Le TP exploite précisément cette différence entre boucles Python et calcul numérique compilé.

Le support renvoie à Pereira et al. (2021) pour une comparaison énergétique entre langages ; il ne développe pas les résultats de cette étude dans ces pages.

### 13. Identifier le goulot d'étranglement — p. 44

Un programme peut passer son temps à calculer, attendre des données ou communiquer. Il faut optimiser ce qui limite effectivement son exécution.

Dans le schéma du cours, les transferts réseau prennent davantage de temps que les calculs. Accélérer seulement le calcul donne donc un gain global limité.

Il est parfois possible de déplacer le coût d'un sous-système vers un autre. Compresser des données ajoute du calcul, mais réduit le volume à transmettre. Cette transformation peut être bénéfique si le temps ou l'énergie gagnés sur le transfert dépassent ceux de la compression.

On peut aussi chevaucher des tâches indépendantes : lire les données suivantes pendant qu'on calcule sur les précédentes, ou transmettre un résultat pendant la préparation du prochain lot. L'objectif est de réduire les périodes où une ressource attend inutilement.

### 14. RAM, adresses et stockage des matrices — p. 45-47

La RAM est la mémoire de travail, distincte du stockage persistant. Le modèle simplifié de l'accès aléatoire signifie qu'il n'est pas nécessaire de déplacer une tête de lecture comme sur un disque mécanique. Cela ne signifie pas que toute suite d'accès aura les mêmes performances : caches, localité, contrôleurs et organisation matérielle interviennent.

**Précision technique :** la page 45 emploie le mot « flash » en parlant de la RAM. La mémoire principale habituelle des ordinateurs est de la **DRAM**, volatile ; la mémoire **flash** est non volatile et notamment utilisée dans les SSD et clés USB. Il faut conserver cette distinction.

Un programme manipule des adresses mémoire. Des blocs sont alloués pour stocker ses données ; un tableau dense permet de représenter ses éléments dans une zone contiguë de son espace d'adressage. Cette contiguïté ne suppose pas que toutes les pages physiques soient voisines.

Le type numérique fixe la taille et l'interprétation des éléments. Un entier ou flottant de 32 bits occupe 4 octets ; un type de 64 bits en occupe 8. **Le fait qu'un CPU soit 64 bits n'oblige pas à n'utiliser que des données de 64 bits.**

Une matrice bidimensionnelle doit être représentée dans une mémoire linéaire. Pour une matrice de M lignes et N colonnes, avec indices à partir de zéro :

```text
Stockage par lignes, row-major : index(i, j) = i × N + j
Stockage par colonnes, column-major : index(i, j) = i + j × M
```

En stockage par lignes, faire varier `j` parcourt des éléments consécutifs. En stockage par colonnes, c'est faire varier `i` qui les parcourt consécutivement. Les tableaux C contigus et les tableaux numériques en ordre C suivent le premier cas ; Fortran utilise traditionnellement le second.

**Précision technique :** une liste Python de listes ne constitue pas automatiquement un bloc numérique contigu. La formulation « Python » de la page 47 doit être comprise dans le contexte des tableaux numériques utilisés et de leur ordre de stockage.

Une représentation à plusieurs niveaux de pointeurs peut faciliter certaines manipulations mais ajouter des indirections et réduire la localité. Le choix de représentation fait donc partie de l'optimisation.

### 15. Caches et topologie mémoire — p. 48-49

Entre le CPU et la RAM, les caches conservent des données pour accélérer leur réutilisation :

```text
Unités de calcul <-> L1 <-> L2 <-> L3 <-> RAM
```

Les niveaux proches du cœur sont généralement plus petits et plus rapides. L'organisation exacte dépend du processeur ; le partage du L3 et le caractère privé des caches inférieurs décrivent l'exemple présenté, pas une règle absolue pour toutes les architectures.

Les transferts se font par **lignes de cache**, c'est-à-dire par blocs. Lire un élément peut donc rendre disponibles ses voisins. Parcourir une zone dans l'ordre et réutiliser les valeurs déjà chargées favorise :

- La **localité spatiale** : utiliser des données voisines.
- La **localité temporelle** : réutiliser rapidement une donnée déjà chargée.

Un *cache miss* signifie que la donnée n'est pas présente au niveau de cache consulté ; il faut alors la chercher plus loin, éventuellement en RAM. Un parcours par colonnes dans un tableau stocké par lignes peut fortement dégrader l'utilisation des lignes de cache.

Le support illustre un Ryzen 9 5900X à 12 cœurs, avec deux ensembles partageant chacun leur L3 et des caches L1/L2 associés aux cœurs. Le placement des tâches et le partage des données peuvent donc influencer les performances de la parallélisation.

### 16. Utiliser le compilateur — p. 50

Un compilateur peut analyser les dépendances du programme puis transformer le code en instructions adaptées au processeur. Il peut supprimer du travail inutile, déplacer certains calculs ou transformer des boucles lorsque les règles du langage l'autorisent.

Le support présente les niveaux GCC `-O1`, `-O2` et `-O3` et des listes d'optimisations associées. Les transformations activées dépendent du compilateur et de sa version : ces listes ne sont pas une spécification universelle.

Le point à retenir est expérimental : comparer le même calcul compilé avec plusieurs niveaux et mesurer. Le niveau le plus agressif n'est pas automatiquement le meilleur dans toutes les situations. L'efficacité du compilateur dépend aussi de la clarté des accès mémoire et des dépendances qu'il doit respecter.

### 17. Pourquoi la multiplication matricielle est le fil conducteur — p. 51-52

Pour A de dimension M × K et B de dimension K × N, le produit C a la dimension M × N :

```text
C[i, j] = somme pour k allant de 0 à K-1 de A[i, k] × B[k, j]
```

L'algorithme classique calcule M × N produits scalaires de longueur K. Son coût est Θ(MNK), donc **Θ(N³)** pour des matrices carrées de côté N. Doubler N multiplie approximativement le travail arithmétique par huit et le stockage des matrices par quatre.

Cette opération se retrouve dans de nombreux problèmes numériques et dans une grande partie du calcul des réseaux de neurones. Elle bénéficie d'instructions et de matériels spécialisés, ainsi que de bibliothèques optimisées.

Le support cite OpenBLAS, Intel MKL, MAGMA, cuBLAS et rocBLAS. Les routines BLAS constituent une référence pour l'algèbre linéaire ; les bibliothèques citées ciblent différents environnements CPU ou accélérés.

Des algorithmes de complexité asymptotique plus faible existent. Cela ne garantit pas qu'ils soient plus efficaces dans le contexte du TP : disposition des données, constantes, tailles et capacités du matériel comptent aussi. Deux implémentations en Θ(N³) peuvent déjà présenter des performances très différentes.

Le TP annoncé suit principalement la ressource *Algorithmica* de Sergey Slotin. Il vise à comparer les implémentations depuis Python jusqu'au GPU, en expliquant les gains et leurs effets énergétiques.

### 18. Ce qu'il faut savoir mobiliser après le cours

1. Définir un besoin et un budget avant de choisir une solution d'IA.
2. Situer un calcul dans le cycle de vie du matériel et les infrastructures qui le rendent possible.
3. Distinguer puissance, énergie et émissions de gaz à effet de serre.
4. Décrire précisément le périmètre d'une mesure et ses conditions thermiques.
5. Identifier si le programme est limité par le calcul, la mémoire ou les communications.
6. Relier l'ordre des boucles et le stockage des données au comportement des caches.
7. Comparer interprétation, compilation, bibliothèque optimisée et parallélisation sur un travail équivalent.
8. Évaluer les économies par tâche et l'évolution du nombre de tâches pour tenir compte du rebond.

<a id="tp1"></a>

## II. Guide précis du TP 1 : multiplication de matrices

### 1. Les objectifs effectivement donnés par le cours

La page 52 fixe six axes :

1. Implémenter et mesurer une multiplication matricielle naïve en Python ; la comparer à des variantes utilisant les outils Python et à NumPy.
2. Étudier l'effet de la compilation : compilation JIT de Python, puis implémentation en C.
3. Développer des versions C de plus en plus optimisées en utilisant l'organisation du système et de la mémoire.
4. Comparer ces versions à OpenBLAS.
5. Explorer la parallélisation CPU avec OpenMP et son effet sur l'énergie.
6. Découvrir des implémentations GPU simples et avancées et comparer leur consommation à celle du CPU.

**Le PDF ne précise pas** les tailles à utiliser, le compilateur et sa version, l'outil JIT, le capteur d'énergie, la marque de GPU, les fichiers à remplir ou les questions exactes du rapport. Les choix chiffrés et le découpage ci-dessous sont une proposition méthodologique pour réaliser ces six objectifs. Ils seront à adapter si un énoncé plus détaillé est distribué.

La progression proposée est :

```text
Préparer -> définir le calcul -> valider -> mesurer Python -> JIT -> C
        -> compilateur -> mémoire et caches -> OpenBLAS -> OpenMP
        -> GPU -> comparaison énergétique -> rapport
```

### 2. Étape 0 — Préparer l'environnement et la fiche machine

**But :** pouvoir expliquer et reproduire les résultats.

À relever avant les expériences :

- Système d'exploitation et environnement réel : Windows natif, WSL, Linux de la salle, etc.
- Modèle de CPU, nombre de cœurs physiques et de processeurs logiques.
- Quantité de RAM, informations sur les caches si disponibles.
- GPU disponible, mémoire et environnement de calcul associé.
- Versions de Python, des bibliothèques utilisées et du compilateur C.
- Bibliothèque BLAS réellement utilisée par la référence NumPy.
- Possibilité de contrôler et de relever le nombre de threads.
- Moyen de mesure d'énergie et composants qu'il couvre.
- Mode d'alimentation, branchement secteur et conditions de refroidissement.

**Sur ce dépôt Windows :** la disponibilité de GCC, d'OpenMP, d'OpenBLAS ou d'un environnement GPU n'a pas été vérifiée dans le cadre de cette synthèse. Ne pas supposer que ces outils sont installés. Choisir l'environnement fourni en cours ou un environnement où ces composants sont compatibles entre eux.

Pour les mesures, réduire les activités concurrentes et garder le même mode d'alimentation. Documenter ce qui ne peut pas être contrôlé plutôt que d'attribuer toute variation à l'algorithme.

**À conserver :** une fiche d'environnement dans le rapport. Une organisation possible du travail comprend un dossier de sources, un dossier de résultats bruts et un dossier de figures ; ces dossiers ne sont pas imposés par le PDF et ne sont pas créés par ce guide.

### 3. Étape 1 — Définir exactement le calcul et ses données

**But :** comparer des versions qui réalisent le même travail.

Fixer le contrat commun :

```text
Entrées : A de dimension M × K ; B de dimension K × N.
Sortie : C = A × B, de dimension M × N.
Chaque exécution repart d'un résultat indépendant de l'exécution précédente.
```

Dans le cas d'une implémentation qui accumule avec `C += ...`, remettre C à zéro avant chaque nouveau produit. Dans une version qui affecte directement chaque `C[i,j]`, vérifier que toutes les cases sont écrites.

Choix proposés pour l'expérience :

1. Utiliser d'abord des données en double précision, 64 bits, pour les versions numériques compilées. Garder cette précision pour les comparaisons directes.
2. Employer des tableaux contigus en ordre par lignes pour le C et les variantes qui reposent sur ce stockage.
3. Générer A et B de façon reproductible, avec une graine fixe, puis réutiliser les mêmes valeurs entre versions comparées.
4. Garder les entrées immuables pendant le calcul.
5. Commencer par de petites tailles, puis augmenter progressivement.

Exemples de tailles de travail, **non imposées par le support** :

| Usage | Dimensions proposées | Intérêt |
| --- | --- | --- |
| Vérification manuelle | 2 × 3 multiplié par 3 × 2. | Détecter une confusion entre indices ou dimensions. |
| Vérification des cas limites | Matrices nulles, identités, dimensions égales à 1. | Détecter une initialisation ou une accumulation incorrecte. |
| Essai des boucles Python | N = 16, 32, 64, puis éventuellement 128. | Éviter de commencer par un calcul très long. |
| Mesure compilée | N = 128, 256, 512, 1 024 ; agrandir si pertinent. | Observer différents régimes de performance et de mémoire. |
| Vérification des bords | Par exemple M = 7, K = 11, N = 5, puis N = 257. | Tester les matrices rectangulaires et les tailles non multiples des blocs. |

Le stockage minimal de A, B et C en 64 bits vaut :

```text
Mémoire en octets = 8 × (M×K + K×N + M×N)
Pour trois matrices N × N : 24 × N² octets
```

Il faut ajouter les copies, transpositions, tampons des bibliothèques et éventuelles données GPU. Les listes et objets Python ont un surcoût supplémentaire que cette formule ne représente pas.

**À conserver :** dimensions, type, ordre de stockage et méthode de génération de chaque jeu de données.

### 4. Étape 2 — Mettre en place la vérification des résultats

**But :** ne jamais interpréter la rapidité d'un calcul incorrect.

1. Calculer un petit exemple dont le résultat est connu.
2. Définir une implémentation de référence, par exemple le produit matriciel NumPy pour les essais plus grands.
3. Vérifier chaque nouvelle version sur les petites matrices, puis sur des données représentatives.
4. Refaire ces vérifications après une modification de l'ordre des opérations, du parallélisme ou du type numérique.

Exemple manuel :

```text
A = [[1, 2, 3],       B = [[ 7,  8],       C = [[ 58,  64],
     [4, 5, 6]]            [ 9, 10],            [139, 154]]
                          [11, 12]]
```

Les arrondis flottants peuvent différer selon l'ordre des additions, les instructions employées et le parallélisme. Pour des flottants, utiliser une comparaison approchée plutôt qu'exiger systématiquement une égalité bit à bit :

```text
|C_test[i,j] - C_ref[i,j]| ≤ atol + rtol × |C_ref[i,j]|
```

Choisir et annoncer `atol` et `rtol` en fonction de la précision, des valeurs et de la longueur des sommes ; le cours ne donne pas de seuil. Vérifier aussi l'absence de valeurs non finies inattendues. Une simple somme de contrôle ne remplace pas cette comparaison, car des erreurs peuvent s'y compenser.

**Critère pour continuer :** la version passe les vérifications numériques, y compris sur des dimensions non carrées et les bords des blocs lorsqu'ils existent.

### 5. Étape 3 — Construire un protocole de mesure commun

**But :** attribuer les écarts observés aux changements étudiés.

Pour chaque configuration :

1. Préparer les données en dehors de la fenêtre mesurée si l'on mesure le calcul seul.
2. Faire les préparations nécessaires : compilation JIT, initialisation de bibliothèque, contexte GPU éventuel.
3. Choisir un régime thermique comparable et le documenter.
4. Effectuer un premier essai non comptabilisé lorsque l'on souhaite mesurer le régime établi.
5. Lancer plusieurs répétitions indépendantes avec le résultat correctement réinitialisé.
6. Enregistrer chaque mesure brute, puis calculer une médiane et un indicateur de dispersion. Cinq à dix répétitions constituent un point de départ proposé, à adapter au coût des expériences.
7. Vérifier le résultat en dehors de la fenêtre chronométrée.

Utiliser un chronomètre monotone adapté aux durées courtes, par exemple `perf_counter` en Python. Pour des calculs trop brefs, mesurer un lot de produits et diviser par leur nombre. Préciser alors si l'on réutilise les mêmes données, car cela modifie le comportement des caches.

Séparer deux questions :

- **Calcul seul** : matrices déjà prêtes dans la mémoire utilisée par le calcul.
- **Opération complète** : inclut les préparations nécessaires à l'usage réel, par exemple transposition, copies et transferts GPU.

Ne pas mélanger ces périmètres dans le même classement. L'allocation, la remise à zéro du résultat et les conversions doivent suivre une convention explicite et cohérente. Une copie de sortie ou une remise à zéro imposée par une variante peut être présentée séparément et incluse dans son coût complet.

Indicateurs utiles, ajoutés ici pour exploiter les mesures :

```text
Travail conventionnel du produit classique ≈ 2 × M × N × K opérations flottantes
GFLOP/s ≈ (2 × M × N × K) / (T_secondes × 10^9)
Accélération = T_référence / T_version
Économie d'énergie relative = 1 - E_version / E_référence
Efficacité énergétique = travail conventionnel / énergie
```

La convention `2MNK` compte une multiplication et une addition séparément, y compris lorsqu'une instruction fusionnée les réalise. Elle décrit le travail mathématique conventionnel, pas le nombre d'instructions machine.

**À conserver :** pour chaque mesure, version, M/K/N, précision, nombre de threads, options de compilation, état de préparation, périmètre temporel et périmètre énergétique.

### 6. Étape 4 — Implémenter la version Python naïve

**Objectif du support :** établir un point de départ simple.

Réaliser le produit avec trois boucles et un accumulateur scalaire :

```text
pour i de 0 à M-1 :
    pour j de 0 à N-1 :
        somme = 0
        pour k de 0 à K-1 :
            somme += A[i,k] × B[k,j]
        C[i,j] = somme
```

À faire :

1. Programmer cette version sans appel à une routine de multiplication matricielle.
2. La vérifier avec les cas de l'étape 2.
3. Mesurer les petites tailles avant d'augmenter N.
4. Calculer les rapports de durée lorsque N double.
5. Expliquer que la tendance cubique peut être perturbée par les coûts fixes, les données et les effets mémoire.

Les boucles Python effectuent beaucoup d'opérations de gestion en plus de l'arithmétique : interprétation, manipulation d'objets et accès aux éléments. Ce point prépare la comparaison avec du code compilé.

**À produire :** une première courbe temps selon N et un tableau des résultats de la version de référence.

### 7. Étape 5 — Comparer les variantes Python et NumPy

**Objectif du support :** mesurer l'effet du niveau d'implémentation.

1. Ajouter une variante exprimant les produits scalaires avec des outils Python tels que `sum`, les itérations et éventuellement une représentation préalable des colonnes.
2. Vérifier qu'elle calcule toujours le même produit.
3. Si la préparation des colonnes nécessite une transposition ou une copie, relever ce coût séparément et dans le coût complet.
4. Comparer avec le produit matriciel NumPy, exprimé par l'opérateur `@` sur des tableaux numériques adaptés.
5. Relever la bibliothèque BLAS sous-jacente et son nombre de threads lorsque c'est possible.
6. Comparer une référence à un thread aux versions à un thread ; présenter ensuite séparément les résultats multithreads.

**Distinction essentielle :** dans ce contexte NumPy, `A * B` est un produit élément par élément, tandis que `A @ B` est un produit matriciel. Python n'offre pas une multiplication matricielle native universelle pour de simples listes de listes : la mention des « built-in implementations » dans le support ne permet pas d'en supposer une.

Question à expliquer dans le rapport : pourquoi une opération écrite en Python peut-elle être beaucoup plus rapide que des boucles Python ? Parce que le calcul lourd peut être effectué par une bibliothèque native compilée et optimisée.

**À produire :** comparaison Python naïf / variante Python / NumPy, avec précision et nombre de threads explicités.

### 8. Étape 6 — Compiler la boucle Python en JIT

**Objectif du support :** isoler l'effet de la compilation avant le passage au C.

Le PDF ne nomme pas l'outil JIT. Utiliser celui fourni en cours ; un compilateur tel que Numba serait un choix possible si aucun outil n'est imposé.

À faire :

1. Adapter la boucle à un mode de compilation numérique effectif sur des tableaux typés.
2. Préserver autant que possible l'algorithme, le type, l'ordre des boucles et l'organisation des données.
3. Exécuter un premier appel pour déclencher la compilation.
4. Distinguer le temps de premier appel et le temps des appels suivants.
5. Mesurer les appels compilés en régime établi.
6. Vérifier la correction et comparer à Python naïf puis à NumPy.

Pour isoler au mieux le gain de compilation, comparer si possible la boucle non compilée et sa version compilée sur la même représentation numérique. Si la version de départ utilise des listes de listes et la version JIT des tableaux contigus, annoncer que **compilation et représentation ont changé**.

Ne pas activer simultanément compilation, parallélisme automatique et assouplissement des règles flottantes si l'on veut comprendre le gain de chaque transformation. Ces pistes peuvent être des expériences ultérieures distinctes.

**À produire :** durée du premier appel, durée en régime établi et facteur d'accélération.

### 9. Étape 7 — Réécrire le produit naïf en C

**Objectif du support :** accéder explicitement au stockage et aux boucles compilées.

1. Stocker A, B et C dans des tableaux numériques contigus.
2. Utiliser d'abord la même boucle `i-j-k` que dans la version naïve.
3. Employer les indices aplatis corrects :

```text
A[i,k] -> a[i × K + k]
B[k,j] -> b[k × N + j]
C[i,j] -> c[i × N + j]
```

4. Vérifier les dimensions et les allocations avant d'exécuter le produit.
5. Comparer les résultats avec la référence.
6. Mesurer uniquement la région définie par le protocole, sans lecture de fichiers, affichage ou génération aléatoire au milieu.
7. Consommer ou contrôler effectivement le résultat après la mesure pour éviter qu'un calcul sans effet observable puisse être supprimé par le compilateur.

La taille mémoire calculée et les indices doivent tenir dans les types entiers utilisés. Une version qui dépasse les limites du tableau n'est pas un benchmark exploitable, même si elle semble rapide.

**À produire :** première comparaison C naïf / JIT / NumPy, à précision et parallélisme comparables.

### 10. Étape 8 — Mesurer les niveaux d'optimisation du compilateur

**Lien au cours :** page 50.

1. Compiler exactement la même version C avec plusieurs niveaux.
2. Utiliser `-O0` comme point de comparaison proposé, puis `-O1`, `-O2` et `-O3` présentés dans le cours, si le compilateur choisi les prend en charge.
3. Conserver le même matériel, les mêmes entrées et les mêmes conditions de mesure.
4. Vérifier les résultats pour chaque exécutable.
5. Mesurer temps et énergie disponible, puis comparer.

Changer une seule option ou un seul groupe bien identifié à la fois. Une option propre au processeur, une modification de l'arithmétique flottante ou une vectorisation manuelle constitue une expérience distincte à documenter.

Ne pas supposer qu'un niveau donné impose une transformation précise : consulter les informations du compilateur utilisé si l'on souhaite attribuer le résultat à une vectorisation ou à une autre optimisation particulière.

**À produire :** un tableau ou graphique associant niveau, temps, débit et énergie lorsque mesurable.

### 11. Étape 9 — Modifier l'ordre des boucles pour améliorer la localité

**Lien au cours :** pages 46-49 ; concrétisation de l'objectif d'optimisation C de la page 52.

Dans la version `i-j-k`, `k` varie dans la boucle intérieure. Pour un stockage par lignes :

- `A[i,k]` est parcouru de façon contiguë.
- `B[k,j]` avance avec un pas de N éléments : on parcourt une colonne.

Une variante `i-k-j` permet de parcourir des lignes de B et de C :

```text
mettre C à zéro
pour i de 0 à M-1 :
    pour k de 0 à K-1 :
        a_ik = A[i,k]
        pour j de 0 à N-1 :
            C[i,j] += a_ik × B[k,j]
```

À faire :

1. Ajouter cette variante sans modifier la précision ou le parallélisme.
2. Vérifier que C est remis à zéro entre deux produits.
3. Refaire les vérifications numériques.
4. Mesurer sur les mêmes tailles.
5. Relier les écarts observés aux accès contigus, à la réutilisation des données et aux possibilités de compilation.

Les six permutations des trois indices peuvent être explorées si le temps et l'énoncé le justifient. Le PDF n'impose ni ces six variantes ni un classement attendu. Les gains dépendent des tailles et du matériel.

**À produire :** une comparaison des ordres retenus et une explication précise des parcours mémoire.

### 12. Étape 10 — Tester une transposition de B

**Proposition méthodologique :** rendre contigus les deux vecteurs lus par un produit scalaire.

Construire BT, de dimension N × K, tel que :

```text
BT[j,k] = B[k,j]
C[i,j] = somme sur k de A[i,k] × BT[j,k]
```

À faire :

1. Mesurer la construction de BT.
2. Mesurer le produit une fois BT prêt.
3. Présenter également la somme des deux pour un produit isolé.
4. Comparer cette version à `i-j-k` et `i-k-j`.
5. Si B est réutilisé dans plusieurs produits, discuter l'amortissement de sa transposition.

La transposition ajoute de la mémoire et des lectures/écritures. Un gain sur le noyau seul n'assure pas un gain sur l'opération complète. Le PDF n'impose pas cette variante précise ; elle illustre son objectif de meilleure utilisation de la mémoire.

**À produire :** temps de préparation, temps de calcul et temps complet.

### 13. Étape 11 — Introduire un calcul par blocs

**Proposition méthodologique :** réutiliser de petits blocs de données pendant qu'ils sont en cache.

Diviser les dimensions en blocs de taille b. Pour une version simple :

```text
mettre C à zéro
pour ii de 0 à M-1 par pas de b :
    pour kk de 0 à K-1 par pas de b :
        pour jj de 0 à N-1 par pas de b :
            pour i de ii à min(ii+b, M)-1 :
                pour k de kk à min(kk+b, K)-1 :
                    a_ik = A[i,k]
                    pour j de jj à min(jj+b, N)-1 :
                        C[i,j] += a_ik × B[k,j]
```

À faire :

1. Commencer par cette organisation simple, puis vérifier les résultats.
2. Tester plusieurs tailles de blocs, par exemple 16, 32 et 64 comme points de départ, sans les considérer comme des optimums prescrits.
3. Inclure des dimensions non multiples de b pour valider les bords.
4. Mesurer pour plusieurs tailles de matrices.
5. Expliquer pourquoi un bloc trop petit ajoute de la gestion et pourquoi un bloc trop grand peut perdre les bénéfices de cache.

Trois blocs carrés de côté b en double précision représentent environ `3 × b² × 8` octets, ce qui donne un ordre de grandeur pour raisonner sur la capacité des caches. Ce calcul ne remplace pas la mesure et ne décrit pas toutes les données actives de l'implémentation.

Une exploration plus avancée peut porter sur le déroulage de boucle, la vectorisation, l'alignement ou le rangement de blocs dans des tampons dédiés. Ce sont des approfondissements possibles ; **le support local ne les détaille pas comme des tâches obligatoires**.

**À produire :** meilleur bloc observé pour chaque taille pertinente et comparaison à la meilleure version sans blocs.

### 14. Étape 12 — Comparer à OpenBLAS

**Objectif explicite de la page 52 :** disposer d'une référence optimisée bas niveau.

1. Exécuter le même produit dense avec OpenBLAS dans l'environnement du TP.
2. Employer la routine et la précision correspondant aux données ; garder les mêmes dimensions et le même sens de multiplication.
3. Vérifier l'ordre de stockage, les éventuelles transpositions et les paramètres de disposition des matrices.
4. Si la routine expose une opération de la forme `C = alpha × A × B + beta × C`, choisir un cas correspondant bien à un nouveau produit, par exemple `alpha = 1` et `beta = 0`.
5. Fixer d'abord la référence à un thread pour comparer aux versions séquentielles.
6. Mesurer ensuite, séparément, son fonctionnement multithread.
7. Comparer à la meilleure version maison et à NumPy.

NumPy peut déjà utiliser OpenBLAS, mais ce n'est pas garanti par le simple fait d'utiliser NumPy. Ne pas présenter deux appels comme utilisant des moteurs différents sans vérifier leur bibliothèque sous-jacente.

L'objectif est de comprendre l'écart avec une bibliothèque spécialisée, pas de promettre qu'une version courte écrite pendant le TP la dépassera.

**À produire :** comparaison à un thread, puis comparaison avec parallélisme annoncé ; ratio de débit par rapport à OpenBLAS.

### 15. Étape 13 — Paralléliser sur CPU avec OpenMP

**Objectif explicite du support :** observer l'accélération et son coût énergétique.

1. Partir d'une version séquentielle correcte et déjà mesurée.
2. Distribuer des lignes ou des blocs de sortie indépendants entre threads.
3. Vérifier qu'un même élément de C n'est pas modifié simultanément sans mécanisme de synchronisation adapté.
4. Garder les accumulateurs temporaires privés au travail qui les utilise.
5. Comparer 1, 2, 4, puis davantage de threads selon le CPU disponible.
6. Distinguer le nombre de cœurs physiques du nombre de processeurs logiques.
7. Contrôler le nombre de threads des bibliothèques appelées à l'intérieur de la zone parallèle.
8. Mesurer temps, énergie disponible et dispersion pour chaque configuration.

**Piège important :** paralléliser naïvement la boucle de réduction en `k` peut conduire plusieurs threads à écrire dans le même `C[i,j]`. Distribuer les lignes ou blocs de C est un point de départ plus simple. Une région OpenMP qui appelle elle-même une BLAS multithread peut également créer trop de threads et perturber la comparaison.

Indicateurs :

```text
Accélération avec p threads : S(p) = T(1) / T(p)
Efficacité parallèle : eta(p) = S(p) / p
```

Présenter ces résultats à problème identique. Expliquer les limites possibles : partie séquentielle, création et coordination des threads, bande passante, caches partagés, placement des threads ou baisse de fréquence sous charge.

La configuration la plus rapide peut être différente de celle qui minimise les joules par produit. C'est précisément une question du TP.

**À produire :** courbes temps et énergie selon le nombre de threads, puis choix argumenté d'une configuration.

### 16. Étape 14 — Étudier le GPU

**Objectif explicite du support :** découvrir des versions simples et avancées, puis comparer au CPU.

L'environnement exact et le code GPU ne figurent pas dans le dépôt local. Utiliser les exemples fournis en cours lorsqu'ils seront disponibles ; ne pas supposer qu'une technologie propre à une marque de GPU est imposée.

Progression proposée :

1. Vérifier que les matrices tiennent en mémoire GPU avec les tampons nécessaires.
2. Transférer A et B sur l'accélérateur.
3. Étudier une version simple où un fil ou groupe de travail produit un ou plusieurs éléments de C.
4. Étudier une version avancée qui réutilise des blocs de données dans une mémoire rapide adaptée à l'architecture, ou comparer à une bibliothèque spécialisée.
5. Synchroniser correctement la fin du travail avant d'arrêter un chronomètre hôte : un lancement asynchrone n'est pas la durée du calcul achevé.
6. Récupérer C et vérifier le résultat.
7. Refaire les mesures pour plusieurs tailles, y compris des tailles où le coût des transferts compte beaucoup.

Publier au moins deux durées :

```text
Temps du noyau GPU : données déjà sur le GPU ; calcul correctement synchronisé.
Temps complet : préparation nécessaire + transfert vers GPU + calcul + retour du résultat.
```

Si l'allocation ou l'initialisation du contexte n'a lieu qu'une fois dans l'usage étudié, l'indiquer et isoler son coût de démarrage.

Garder la même précision numérique pour une comparaison directe. Si une autre précision ou un mode de calcul approché est étudié, créer une comparaison séparée incluant l'erreur observée.

Pour l'énergie, préciser si le capteur couvre seulement le GPU, le CPU, ou toute la machine. Comparer une énergie GPU seule à une énergie de machine entière ne permet pas de conclure directement sur l'économie globale. Un temps complet associé à une énergie du noyau seul doit également être identifié comme tel.

**À produire :** comparaison CPU/GPU selon N, distinction noyau/opération complète et limites du périmètre énergétique.

### 17. Étape 15 — Mesurer l'énergie de façon exploitable

Cette étape accompagne les précédentes ; il n'est pas nécessaire d'attendre le GPU pour commencer les mesures énergétiques.

**Si un capteur de puissance est disponible :**

1. Identifier le composant ou l'ensemble couvert et la fréquence d'échantillonnage.
2. Mesurer une référence au repos dans des conditions pertinentes si l'on veut isoler la consommation supplémentaire.
3. Mettre la machine dans l'état thermique choisi.
4. Démarrer une séquence de calcul suffisamment longue pour être observable par le capteur.
5. Relever la puissance sur la même fenêtre que celle du travail exécuté.
6. Intégrer les échantillons sur la durée.
7. Diviser par le nombre de produits si l'on a mesuré un lot.
8. Répéter et présenter la variabilité.

**Si un compteur d'énergie est disponible :** relever la différence entre début et fin, en tenant compte des unités et d'un éventuel retour à zéro du compteur. Ne pas additionner des domaines de mesure qui se recouvrent, par exemple un total CPU et une partie de ce même total.

Approximations utiles lorsque leurs hypothèses sont acceptables :

```text
Énergie totale ≈ somme de P_charge(t_l) × Δt_l
Énergie supplémentaire ≈ somme de [P_charge(t_l) - P_repos] × Δt_l
Énergie par produit = énergie de la séquence / nombre de produits
```

Une variation importante du repos ou un échantillonnage trop grossier doit figurer dans les limites de l'expérience. Ne pas corriger arbitrairement des mesures incohérentes pour obtenir l'ordre attendu.

**En l'absence de capteur exploitable :** mesurer les temps et annoncer que l'énergie n'a pas été mesurée. La puissance nominale d'un composant ou son TDP n'est pas une mesure de la puissance réellement consommée par chaque variante. Un gain de temps ne démontre pas à lui seul un gain énergétique.

La mesure électrique ne constitue pas non plus une analyse complète du cycle de vie. Une conversion de l'électricité en CO₂e nécessiterait un facteur d'émission explicite et ne couvrirait pas automatiquement la fabrication ou les autres impacts.

**À produire :** énergie totale ou supplémentaire clairement nommée, en joules par produit, avec source de mesure et limites.

### 18. Étape 16 — Consolider les résultats et rédiger le rapport

Table de travail proposée ; les colonnes d'énergie restent vides ou marquées « non mesuré » lorsqu'aucune mesure n'a été réalisée :

| Version | M/K/N | Précision | Threads | Préparation incluse ? | Temps médian (s) | Dispersion | GFLOP/s | Énergie (J/produit) | Domaine mesuré | Erreur numérique |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Python naïf | À renseigner | À renseigner | À renseigner | À renseigner | À mesurer | À mesurer | À calculer | À mesurer | À décrire | À vérifier |
| Python avec outils intégrés | À renseigner | À renseigner | À renseigner | À renseigner | À mesurer | À mesurer | À calculer | À mesurer | À décrire | À vérifier |
| NumPy | À renseigner | À renseigner | À renseigner | À renseigner | À mesurer | À mesurer | À calculer | À mesurer | À décrire | À vérifier |
| JIT, régime établi | À renseigner | À renseigner | À renseigner | À renseigner | À mesurer | À mesurer | À calculer | À mesurer | À décrire | À vérifier |
| C naïf, options précisées | À renseigner | À renseigner | À renseigner | À renseigner | À mesurer | À mesurer | À calculer | À mesurer | À décrire | À vérifier |
| C, boucles réordonnées | À renseigner | À renseigner | À renseigner | À renseigner | À mesurer | À mesurer | À calculer | À mesurer | À décrire | À vérifier |
| C, B transposée | À renseigner | À renseigner | À renseigner | À renseigner | À mesurer | À mesurer | À calculer | À mesurer | À décrire | À vérifier |
| C, calcul par blocs | À renseigner | À renseigner | À renseigner | À renseigner | À mesurer | À mesurer | À calculer | À mesurer | À décrire | À vérifier |
| OpenBLAS | À renseigner | À renseigner | À renseigner | À renseigner | À mesurer | À mesurer | À calculer | À mesurer | À décrire | À vérifier |
| OpenMP | À renseigner | À renseigner | À renseigner | À renseigner | À mesurer | À mesurer | À calculer | À mesurer | À décrire | À vérifier |
| GPU, noyau seul | À renseigner | À renseigner | À décrire | Non | À mesurer | À mesurer | À calculer | À mesurer | À décrire | À vérifier |
| GPU, opération complète | À renseigner | À renseigner | À décrire | Oui | À mesurer | À mesurer | À calculer | À mesurer | À décrire | À vérifier |

Lignes à dupliquer pour chaque dimension, nombre de threads, niveau de compilation et autre paramètre étudié. Ne pas publier un seul chiffre sans les conditions qui lui donnent son sens.

Figures proposées, selon les expériences effectivement réalisées :

1. Temps selon N pour les grandes familles d'implémentation.
2. Débit en GFLOP/s selon N pour les versions compilées et les références.
3. Comparaison des ordres de boucles et tailles de blocs.
4. Accélération et efficacité parallèle selon le nombre de threads.
5. Joules par produit selon la version et le nombre de threads.
6. CPU/GPU avec distinction entre calcul seul et opération complète.

Trame proposée du rapport :

1. **Problème et objectif** : calcul réalisé, besoin d'efficacité, questions comparées.
2. **Environnement** : machine, logiciels et périmètre énergétique.
3. **Protocole** : données, précision, validation, échauffement, répétitions et chronométrage.
4. **Progression des versions** : changement introduit, effet attendu et résultat réellement observé.
5. **Résultats** : tables et figures avec unités, conditions et dispersion.
6. **Analyse** : interprétation par le compilateur, les caches, les communications et le parallélisme.
7. **Énergie et limites** : meilleur temps, meilleure énergie, périmètres incomplets et incertitudes.
8. **Choix final** : implémentation recommandée pour un besoin et un contexte précis.

Les questions à traiter sont notamment :

- Quelle part du gain vient de la compilation, de la mémoire ou du parallélisme ?
- Les variantes effectuent-elles réellement le même travail avec la même précision ?
- Un ordre de boucle change-t-il les performances sans changer la complexité Θ(N³) ?
- Le meilleur nombre de threads pour le temps est-il aussi le meilleur pour l'énergie ?
- La transposition ou les transferts GPU sont-ils amortis dans l'usage considéré ?
- Les données permettent-elles de conclure sur l'énergie, ou seulement sur le temps ?
- À périmètre comparable, quel compromis répond au besoin fixé ?

### 19. Liste de vérification avant de rendre le TP 1

- [ ] Le matériel, les versions et les outils sont décrits.
- [ ] Les matrices, leur précision, leurs dimensions et leur stockage sont explicités.
- [ ] Chaque version a été vérifiée numériquement.
- [ ] Les variantes par blocs gèrent les dimensions non multiples des blocs.
- [ ] Le résultat est correctement réinitialisé ou entièrement réécrit à chaque exécution.
- [ ] Les temps de compilation JIT et de démarrage sont séparés du régime établi.
- [ ] Les copies, transpositions, allocations et transferts suivent un périmètre annoncé.
- [ ] Les calculs GPU sont achevés avant la fin de leur chronométrage.
- [ ] Les nombres de threads maison et BLAS sont connus ou leurs limites sont signalées.
- [ ] Plusieurs mesures et leur dispersion sont conservées.
- [ ] Les watts et les joules ne sont pas confondus.
- [ ] Les domaines de mesure CPU, GPU et machine entière sont distingués.
- [ ] Toute absence de mesure d'énergie est explicitement annoncée.
- [ ] Les conclusions reposent sur des résultats mesurés, sans chiffres inventés.
- [ ] Les choix finaux sont reliés au besoin et au budget de ressources.

<a id="tp2"></a>

## III. TP 2 : ce qui est annoncé et comment le préparer

### 1. Les informations disponibles

Les pages 2 et 19 annoncent une seconde partie sur l'architecture des réseaux de neurones et un **TP de classification d'images sous budget énergétique défini**.

Les objectifs annoncés sont : présenter les composants classiques des réseaux, comprendre leur coût de calcul et relier les choix d'architecture à l'expressivité du modèle et à l'efficacité.

La version locale du PDF ne contient pas encore :

- Le jeu de données et sa répartition.
- L'architecture initiale à utiliser.
- Le framework, les scripts ou les notebooks du TP.
- La valeur du budget et son unité.
- Le périmètre du budget : entraînement, inférence, recherche de modèles ou combinaison de ces coûts.
- Le niveau de qualité minimal et les règles exactes d'évaluation.
- Les expériences d'architecture demandées et les modalités de rendu spécifiques.

On ne peut donc pas décrire les consignes officielles exactes du TP 2 à partir du seul support actuel. Il ne faut pas supposer un dataset, un nombre de couches ou un budget qui n'y figurent pas.

### 2. Démarche préparatoire proposée

La séquence suivante est une **proposition de méthode**, à appliquer une fois les paramètres de l'énoncé connus.

| Étape | Actions à réaliser | Résultat à conserver |
| --- | --- | --- |
| 1. Définir la contrainte | Relever le budget, son unité, les composants couverts, les coûts inclus et le niveau de qualité demandé. | Contrat d'évaluation explicite. |
| 2. Préparer les données | Utiliser les séparations entraînement/validation/test demandées et les mêmes traitements entre essais comparables. | Protocole reproductible, sans utilisation du test pour choisir les modèles. |
| 3. Mesurer une référence | Entraîner ou évaluer le modèle initial selon l'énoncé ; relever qualité, durée, énergie et coût d'inférence pertinent. | Point de départ pour juger les modifications. |
| 4. Identifier les coûts | Repérer les couches, opérations ou transferts qui dominent réellement le travail. | Priorités d'optimisation justifiées. |
| 5. Modifier progressivement | Faire varier un choix d'architecture à la fois : par exemple largeur, profondeur ou taille d'entrée si l'énoncé l'autorise. | Série d'essais interprétables. |
| 6. Comptabiliser les essais | Suivre l'énergie des entraînements et évaluations si elle entre dans le budget ; éviter de compter uniquement le modèle retenu. | Consommation cumulée et budget restant. |
| 7. Comparer les compromis | Confronter qualité, énergie, latence et mémoire dans les conditions d'usage demandées. | Configurations intéressantes et limites de chacune. |
| 8. Sélectionner et évaluer | Choisir avec la validation, puis utiliser le test final selon le protocole imposé. | Résultat final et respect démontré de la contrainte. |

Le nombre de paramètres est une information utile, mais pas une mesure directe d'énergie. Un modèle plus petit peut utiliser des opérations moins adaptées au matériel ou générer davantage de déplacements de données. Il faut comparer le comportement réel.

Lorsque l'on connaît les coûts, une grille d'analyse possible est :

```text
Énergie de recherche : somme des essais exploratoires concernés par le budget.
Énergie d'entraînement final : coût de production du modèle retenu.
Énergie d'inférence : coût par exemple ou par lot, aux conditions annoncées.
Énergie d'usage sur Q prédictions : environ Q × énergie par prédiction,
si les conditions d'exécution et l'attribution de la consommation restent comparables.
```

Ces catégories servent à préciser le périmètre ; elles ne présument pas de ce qui sera effectivement comptabilisé par l'enseignant.

Le rapport devra expliquer le service obtenu dans le budget, pas seulement présenter la meilleure précision. Les techniques non décrites dans le PDF, telles que certaines méthodes de compression de modèles, ne doivent pas être présentées comme des tâches obligatoires du cours.

<a id="correspondance"></a>

## IV. Correspondance avec les 52 pages du support

Cette table permet de retrouver les thèmes et de vérifier la couverture de la synthèse.

| Pages du PDF | Contenu | Où le retrouver ici |
| --- | --- | --- |
| 1 | Titre, intervenants et contexte PSL Week. | Présentation du document et I.1. |
| 2 | Programme provisoire, calendrier et validation. | I.1 et III.1. |
| 3 | Matériel pédagogique, dépôt et précautions de stockage en salle. | I.1. |
| 4 | Trajectoires climatiques du GIEC. | I.2. |
| 5 | Définition générale de l'IA et lien aux infrastructures numériques. | I.2. |
| 6 | Diversité des usages des TIC. | I.2. |
| 7 | Ordres de grandeur des émissions et croissance du numérique. | I.2. |
| 8 | Terminaux, réseaux, centres de données et variations d'estimation. | I.2. |
| 9 | Cycle de vie, fabrication et durée d'utilisation. | I.3. |
| 10 | Intensité carbone de l'électricité et mondialisation du cycle de vie. | I.3. |
| 11 | Chaîne d'approvisionnement et composition d'un smartphone. | I.3. |
| 12 | Diversité des éléments chimiques dans un smartphone. | I.3. |
| 13 | Impacts environnementaux autres que le climat. | I.3. |
| 14 | GPU, histoire industrielle et croissance des investissements IA. | I.4. |
| 15 | Boucle entre capacités disponibles et usages. | I.4. |
| 16 | Trajectoires d'énergie et d'émissions des centres de données. | I.4. |
| 17 | Besoin, budget, choix de conception et de déploiement. | I.4. |
| 18 | Questions ouvertes, géopolitique, déchets et EcoInfo. | I.4. |
| 19 | Objectifs pédagogiques et annonce des deux TP. | I.1, II.1 et III.1. |
| 20 | Du code de haut niveau au code machine. | I.5. |
| 21 | Diversité des formes d'ordinateurs. | I.5. |
| 22 | Composants d'un ordinateur. | I.5. |
| 23-24 | CPU, cœurs et organisation interne d'une puce. | I.5. |
| 25 | IPC, fréquence, boost, multicœur et multithreading matériel. | I.6. |
| 26 | Évolution historique des performances et de l'intégration. | I.6. |
| 27 | Fabrication des CPU et variabilité. | I.6. |
| 28 | Consommation de base et différence entre serveur réel et idéal. | I.7. |
| 29 | État thermique et calcul de l'énergie d'une tâche. | I.7 et II.17. |
| 30 | Puissances différentes malgré une utilisation CPU de 100 %. | I.7. |
| 31-32 | Compromis fréquence, puissance, durée et énergie. | I.8. |
| 33 | Compromis coût, efficacité et performance selon les puces. | I.8. |
| 34 | Mémoire partagée et mémoire distribuée. | I.9. |
| 35 | Coûts d'infrastructure d'un centre de données. | I.9. |
| 36 | Dimensionnement sur les pointes de charge et sous-utilisation. | I.9. |
| 37-38 | TOP500, Green500 et distinction performance/efficacité. | I.9. |
| 39 | Leviers d'amélioration à plusieurs échelles. | I.10. |
| 40 | Effet rebond et paradoxe de Jevons. | I.11. |
| 41 | Contraintes historiques de la programmation. | I.12. |
| 42 | Priorités du développement moderne et coûts des abstractions. | I.12. |
| 43 | Compilation, interprétation et comparaison entre langages. | I.12. |
| 44 | Goulots d'étranglement, compression et chevauchement des tâches. | I.13. |
| 45 | RAM et accès aux données. | I.14. |
| 46 | Adresses, allocation et contiguïté. | I.14. |
| 47 | Stockage par lignes ou par colonnes. | I.14 et II.11. |
| 48 | Caches, lignes de cache et défauts de cache. | I.15. |
| 49 | Topologie mémoire du système d'exemple. | I.15. |
| 50 | Rôle du compilateur et niveaux d'optimisation. | I.16 et II.10. |
| 51 | Produit matriciel, complexité et bibliothèques BLAS. | I.17 et II.3. |
| 52 | Objectifs et progression générale du TP 1. | II.1 à II.19. |

Les sources mentionnées dans le cours comprennent notamment le GIEC, l'ADEME, les travaux et présentations d'Anne-Cécile Orgerie, une analyse de cycle de vie Samsung, le Shift Project, des illustrations de David Guyon, EcoInfo, Pereira et al. et *Algorithmica* de Sergey Slotin. Cette synthèse rend compte de leur utilisation **dans le support local** ; elle ne constitue pas une consultation ou une vérification indépendante de ces sources externes.

<a id="glossaire"></a>

## V. Glossaire

| Terme | Définition utile pour ce cours |
| --- | --- |
| IA frugale | Démarche visant un service défini avec un budget de ressources maîtrisé, en travaillant sur le besoin, les modèles, le code et le matériel. |
| TIC / ICT | Technologies de l'information et de la communication. |
| CO₂e | Unité qui exprime l'effet climatique de différents gaz à effet de serre en équivalent CO₂. |
| Analyse de cycle de vie | Évaluation des impacts depuis les matières premières jusqu'à la fin de vie, sur un périmètre défini. |
| Puissance | Quantité d'énergie par unité de temps, exprimée ici en watts. |
| Énergie | Quantité consommée sur une durée, exprimée ici en joules ou en Wh. |
| Consommation de base | Énergie ou puissance nécessaire au maintien de l'infrastructure même sans le calcul étudié. |
| CPU | Processeur généraliste exécutant les instructions du programme. |
| GPU | Processeur adapté à de nombreux calculs parallèles. |
| FPGA / NPU | Exemples d'accélérateurs : circuit reconfigurable / unité spécialisée pour des calculs de réseaux de neurones. |
| IPC | Nombre d'instructions exécutées par cycle dans les conditions considérées. |
| Cœur physique / fil logique | Unité physique d'exécution / contexte matériel d'exécution pouvant partager un cœur avec d'autres fils. |
| RAM / DRAM | Mémoire de travail ; la DRAM est une technologie habituelle de mémoire principale volatile. |
| Flash | Mémoire non volatile, utilisée notamment dans les SSD. |
| Cache | Mémoire rapide conservant des données pour éviter des accès plus coûteux. |
| Ligne de cache | Bloc élémentaire de données transféré et conservé par un cache. |
| Cache miss | Absence d'une donnée au niveau de cache consulté. |
| Localité | Propriété d'un accès qui favorise la proximité des données ou leur réutilisation rapide. |
| Row-major / column-major | Rangement des éléments d'une matrice par lignes / par colonnes. |
| Goulot d'étranglement | Ressource ou étape qui limite principalement la performance globale. |
| Compilation JIT | Compilation effectuée à l'exécution, dont le coût de démarrage doit être distingué du régime établi. |
| BLAS | Ensemble d'opérations et d'interfaces de base d'algèbre linéaire, implémentées par des bibliothèques spécialisées. |
| OpenBLAS | Une bibliothèque optimisée fournissant notamment des opérations BLAS. |
| OpenMP | Outils de programmation parallèle notamment employés en C sur mémoire partagée. |
| FLOP / GFLOP/s | Opération flottante / milliard d'opérations flottantes par seconde selon la convention de comptage annoncée. |
| Calcul par blocs | Organisation du calcul sur des sous-matrices pour favoriser la réutilisation des données. |
| Effet rebond | Hausse des usages ou d'autres consommations pouvant absorber les gains d'efficacité. |



