# IA frugale : fiche à retenir pour comprendre et optimiser CPU et GPU

**Objectif :** comprendre les mécanismes qui expliquent les performances, puis choisir des optimisations mesurables pour les TP.

**Source principale :** [support du cours](frugal_ai.pdf), David Cornu et Aristide Doussot, PSL Week 2026, version de 52 pages. Les mentions « cours, p. … » renvoient à ce fichier.

**Périmètre :** les notions du cours sont reformulées et illustrées. Les explications détaillées des politiques de cache et du GPU sont des **compléments techniques** : le PDF actuel les survole ou annonce leur étude ultérieure. Leurs sources officielles sont indiquées. Les tailles et organisations mémoire dépendent du matériel ; les exemples ne sont pas des spécifications universelles.

## 1. Les réflexes essentiels

1. Définir le besoin et le budget avant de choisir le matériel et l'algorithme.
2. Vérifier le résultat avant d'interpréter la vitesse.
3. Identifier la limite réelle : calcul, mémoire, transferts ou synchronisation.
4. Parcourir les données dans leur ordre de stockage et réutiliser les données proches du processeur.
5. Éviter les copies et allocations inutiles.
6. Utiliser le compilateur et les bibliothèques optimisées.
7. Paralléliser un travail suffisamment grand et indépendant.
8. Comparer le coût complet, notamment les transferts CPU↔GPU.
9. Mesurer les joules par tâche, pas seulement les secondes ou les watts.

## 2. CPU, fréquence, IPC et utilisation

Le **CPU** exécute des instructions : calculs, lectures/écritures mémoire, comparaisons, branchements, etc. Plusieurs cœurs physiques peuvent traiter des tâches en parallèle.

- **Fréquence** : nombre de cycles d'horloge par seconde. `3 GHz = 3 milliards de cycles/s`.
- **IPC, Instructions Per Cycle** : nombre d'instructions exécutées en moyenne par cycle pour un programme donné.
- À IPC moyen 2 et fréquence 3 GHz, le débit est de l'ordre de `6 milliards d'instructions/s`. Ce n'est pas directement un nombre de FLOP/s : une instruction peut représenter plusieurs opérations.
- **Thread logique** : contexte d'exécution matériel. Deux threads logiques sur un cœur partagent des ressources ; ils ne constituent pas deux cœurs physiques indépendants.

L'IPC dépend du programme : attente de données, dépendances entre instructions, branchements, etc. Augmenter la fréquence ne supprime pas tous ces délais.

**100 % d'utilisation CPU ne signifie pas puissance maximale ni utilisation optimale de toutes les unités.** Deux programmes peuvent solliciter des circuits différents et consommer des puissances différentes. Le CPU peut aussi être compté comme occupé tout en subissant des attentes mémoire. *(Cours, p. 23-30.)*

## 3. RAM, L3, L2, L1 et registres : quels compromis ?

Le compromis est **capacité / latence / débit / coût matériel**. Une très grande mémoire aussi rapide que les registres ou L1 coûterait beaucoup en surface et en ressources matérielles.

```text
Unités de calcul <-> registres <-> L1 <-> L2 <-> L3 <-> RAM
                   très petit                         beaucoup plus grand
                   accès très rapide                  accès plus coûteux
```

Ce schéma est pédagogique : les accès réels peuvent être anticipés, chevauchés ou acheminés différemment.

| Niveau | Rôle | Compromis |
| --- | --- | --- |
| Registres | Valeurs directement utilisées par les instructions, dont les accumulateurs. | Très rapides et peu nombreux ; trop de valeurs actives peuvent provoquer des sauvegardes en mémoire, les *spills*. |
| L1 données | Données immédiatement utiles au cœur. | Très faible latence, faible capacité. Souvent distinct du cache d'instructions. |
| L2 | Ensemble de travail plus grand proche du cœur. | Plus grand, généralement plus lent que L1. Souvent privé par cœur, selon le CPU. |
| L3 / LLC | Dernier niveau de cache sur de nombreux CPU. | Plus grand, souvent partagé entre plusieurs cœurs ; partage et accès plus coûteux. |
| RAM | Données de travail dépassant les caches. | Grande capacité, latence plus élevée, bande passante partagée. |
| SSD / stockage | Conservation persistante des fichiers. | Distinct de la RAM ; accès généralement bien plus coûteux. |

La RAM principale habituelle est de la **DRAM**, volatile. Les caches utilisent généralement de la **SRAM**. La mémoire **flash**, notamment utilisée dans les SSD, est différente : la formulation de la page 45 ne doit pas conduire à les confondre.

**Latence** = délai pour obtenir une donnée. **Bande passante** = quantité de données transférable par seconde. Des lectures dispersées peuvent souffrir de latence ; de grands parcours continus peuvent saturer la bande passante.

**Une matrice n'a pas besoin de tenir entièrement dans L1.** Il faut surtout y réutiliser les parties nécessaires au calcul en cours. Les autres données du programme occupent aussi les caches.

Le cours montre un CPU où des groupes de cœurs partagent des L3 distincts. La proximité des données et le placement du travail comptent donc. L'organisation change selon les générations : voir [Intel : variations de hiérarchie et de partage des caches](https://www.intel.com/content/www/us/en/support/articles/000027820/processors/intel-xeon-processors.html). *(Cours, p. 45 et 48-49 ; complément.)*

## 4. Comment une donnée entre-t-elle dans les caches ?

### Lecture : hit, miss et ligne de cache

**Cas simplifié :** pour une donnée absente de L1, le matériel recherche une copie utilisable à un autre niveau, éventuellement en RAM ou dans le cache d'un autre cœur. Il remplit les niveaux appropriés selon son architecture.

- **Cache hit** : donnée présente au niveau consulté.
- **Cache miss** : donnée absente à ce niveau. Un miss L1 résolu par L2 n'impose pas une lecture en RAM.
- Le **prefetch**, ou préchargement, peut anticiper des accès, notamment réguliers.

Le matériel transfère des **lignes de cache**, pas seulement la valeur demandée. Une ligne vaut couramment **64 octets sur les CPU x86 évoqués ici** : 8 nombres de 64 bits ou 16 nombres de 32 bits.

Exemple, avec un tableau de nombres de 64 bits dont le début est aligné sur une ligne : lire `a[0]` peut charger la ligne contenant `a[0]` à `a[7]`. Les accès suivants à ces voisins peuvent utiliser cette ligne déjà présente.

Ce n'est pas une copie de tout le tableau. Les données peuvent aussi être déjà en cache ; chaque lecture ne déclenche donc pas systématiquement un nouveau transfert.

### « Comment copie-t-on de L2 vers L3 ? »

**Dans du code numérique ordinaire, on ne demande pas directement cette copie.** On lit et écrit des adresses ; les contrôleurs matériels gèrent les caches. Une allocation mémoire ne réserve pas une place particulière dans L1 ou L2.

Pour faire de la place, un cache peut **évincer** une ligne :

- Si elle est **propre**, une autre copie à jour permet souvent de l'abandonner sans réécrire les données.
- Si elle est **modifiée**, dite *dirty*, sa valeur doit être conservée. Une politique **write-back** la réécrit vers un niveau approprié lorsque nécessaire, notamment à l'éviction.

Une éviction de ligne modifiée de L2 peut donc entraîner une écriture vers L3. **Cela ne signifie pas que toutes les données passent obligatoirement et immédiatement par tous les niveaux dans un ordre strict.** Les chemins et politiques varient selon le CPU.

Après une écriture, la RAM ne contient pas nécessairement immédiatement la nouvelle valeur : celle-ci peut d'abord être dans les buffers d'écriture et les caches.

**Inclusif / non inclusif :** un cache inclusif impose la présence des lignes correspondant aux niveaux qu'il inclut ; cela facilite certains suivis mais duplique de la capacité. Un cache non inclusif n'impose pas cette présence systématique. Avec le write-back, la copie la plus récente peut rester proche du cœur.

**Le levier du programmeur est donc l'ordre des accès, la taille des blocs et la réutilisation**, plutôt que des copies manuelles L2→L3. *(Cours, p. 48 ; compléments : [manuel Intel, lectures/écritures et caches](https://cdrdv2-public.intel.com/814199/356477-Optimization-Reference-Manual-V2-002.pdf), [politiques d'inclusion](https://www.intel.com/content/www/us/en/support/articles/000027820/processors/intel-xeon-processors.html).)*

## 5. Localité : pourquoi les optimisations mémoire fonctionnent

| Notion | Principe | Exemple |
| --- | --- | --- |
| Localité spatiale | Utiliser des données voisines. | Parcourir un tableau avec un pas de 1 élément. |
| Localité temporelle | Réutiliser rapidement une donnée. | Réemployer un coefficient ou un bloc avant son éviction. |
| Ensemble de travail | Données nécessaires pendant une phase. | Choisir des blocs compatibles avec les ressources rapides. |

Parcourir une grande matrice entière puis revenir au début peut laisser le temps aux données d'être évincées. Travailler sur un bloc et le réutiliser immédiatement favorise les hits.

Les caches conservent des copies et suivent leurs modifications : une donnée en cache n'est pas « déplacée définitivement hors de la RAM ». *(Cours, p. 48-49 ; complément.)*

## 6. Comment les arrays et matrices sont-ils stockés ?

### Tableau numérique contigu

```text
Éléments : a[0]     a[1]       a[2]       a[3] ...
Adresses : base     base+s     base+2s     base+3s ...
s = taille d'un élément en octets
```

Un `float32` occupe 4 octets ; un `float64`, 8. Un CPU 64 bits peut calculer sur des données de 32 bits.

Pour une matrice M × N stockée **par lignes, row-major** :

```text
Matrice :        a00 a01 a02
                 a10 a11 a12
Mémoire :        a00 a01 a02 a10 a11 a12
Indice aplati :  i × N + j
Adresse :        base + taille_element × (i × N + j)
```

En stockage **par colonnes, column-major** :

```text
Mémoire :        a00 a10 a01 a11 a02 a12
Indice aplati :  i + j × M
```

Un tableau C dense tel que `double a[2][3]` est stocké par lignes. Un tableau de pointeurs tel que `double **` ne garantit pas la contiguïté de toutes les lignes.

### En Python : le conteneur compte

- Une **liste Python** contient des références vers des objets, pas un bloc de nombres bruts équivalent à un tableau C.
- Une **liste de listes** référence des lignes distinctes : toute la matrice n'est pas nécessairement contiguë.
- Un **tableau numérique typé**, notamment NumPy, peut avoir un bloc contigu. Son ordre et ses *strides* déterminent le parcours réel des données.

Un **stride** est le déplacement en octets quand un indice augmente de 1. Pour une matrice contiguë M × N en 64 bits stockée par lignes : stride des lignes = `8N`, stride des colonnes = `8`.

Une transposition peut être une **vue** changeant les strides sans déplacer les données. Elle ne garantit pas que le parcours souhaité devienne contigu. Une **copie réorganisée** peut le rendre contigu, mais coûte du temps et de la mémoire. *(Cours, p. 46-47 ; compléments de représentation.)*

## 7. Double boucle : quel ordre est favorable ?

**Pour un parcours simple, faire varier dans la boucle interne l'indice qui avance le moins loin en mémoire.**

Pour une matrice contiguë stockée par lignes :

```python
# Pseudocode : les voisins d'une même ligne sont contigus.
for i in range(M):          # Boucle externe sur les lignes
    for j in range(N):      # Boucle interne sur les colonnes
        utiliser(A[i, j])
```

Avec les boucles inversées, deux accès successifs sont espacés de `N × taille_element` octets. On risque de charger des voisins qui ne seront réutilisés que trop tard.

**Exemple :** pour 1 024 colonnes en 64 bits, avancer d'une colonne fait un pas de 8 octets ; avancer d'une ligne fait un pas de 8 192 octets. Un parcours par colonnes peut utiliser une seule valeur d'une ligne de cache avant de passer à une autre.

| Stockage | Boucle externe favorable | Boucle interne favorable |
| --- | --- | --- |
| Par lignes, ordre C | Lignes `i` | Colonnes `j` |
| Par colonnes, ordre Fortran | Colonnes `j` | Lignes `i` |

**Il n'existe pas un ordre universellement bon pour toute double boucle.** Il dépend des strides, des tableaux lus/écrits et des dépendances. Plusieurs tableaux peuvent avoir des dispositions incompatibles.

Pour une liste de listes, parcourir une ligne à la fois évite aussi de passer sans cesse d'une liste à l'autre, mais ne signifie pas que tous les nombres sont contigus comme dans un tableau numérique.

Avec des tableaux numériques, utiliser une opération compilée ou vectorisée est généralement un levier plus important que de seulement réordonner des boucles Python. La taille des données, les caches et le compilateur peuvent aussi atténuer les écarts. **Expliquer l'ordre favorable avec les adresses, puis mesurer.** *(Cours, p. 47-48 ; exemples pédagogiques.)*

## 8. Qu'est-ce qu'un langage compilé ?

Un **compilateur** traduit le code source en une autre représentation, notamment en code machine exécutable. Pour le C du TP, cette traduction se fait avant le lancement :

```text
Code C -> compilation et édition de liens -> exécutable -> exécution par le CPU
```

L'**édition de liens** assemble le code compilé et les références aux bibliothèques nécessaires. Un changement de source nécessite normalement de reconstruire l'exécutable.

Un **interpréteur** exécute le programme par l'intermédiaire d'un environnement qui traite ses instructions. Dans CPython, le code est notamment traduit en bytecode, puis exécuté par l'interpréteur. Les boucles numériques peuvent payer des coûts de gestion d'objets et de types à chaque itération.

La **compilation JIT**, *Just-In-Time*, produit du code compilé pendant l'exécution, souvent spécialisé pour certains types. Le premier appel peut inclure un coût absent des suivants.

**Compilé et interprété décrivent des modes d'implémentation, pas deux catégories absolues de langages.** Un programme Python peut appeler une bibliothèque native compilée. Un produit matriciel NumPy peut ainsi déléguer les calculs à une BLAS optimisée au lieu de réaliser les multiplications dans des boucles Python.

| Mode | Intérêt | Coût ou limite |
| --- | --- | --- |
| Compilation avant exécution | Analyse et optimisation avant le calcul. | Construction préalable, cible matérielle et dépendances. |
| Interprétation | Souplesse et environnement interactif. | Surcoûts pour beaucoup de petites opérations individuelles. |
| JIT | Production de code spécialisé à l'exécution. | Coût initial et possibles recompilations. |
| Bibliothèque native | Noyau spécialisé déjà optimisé. | Appel, conversions et disposition des données. |

*(Cours, p. 20 et 42-43 ; précisions pédagogiques.)*

## 9. Les optimisations concrètes sur CPU

### Compilateur, SIMD et registres

Les niveaux GCC `-O1`, `-O2` et `-O3` activent des ensembles d'optimisations. Leur contenu dépend de la version et de la cible ; `-O3` ne garantit pas le meilleur résultat. `-O0` fournit un point de comparaison sans les optimisations usuelles.

Le compilateur peut supprimer du travail inutile, sortir des calculs invariants d'une boucle et transformer certaines boucles. Les dépendances ou l'incertitude sur les accès peuvent limiter ces transformations.

**SIMD** signifie traiter plusieurs valeurs avec une instruction vectorielle. C'est distinct du multicœur : chaque cœur peut utiliser des instructions vectorielles pendant que plusieurs cœurs travaillent. Des accès réguliers et des itérations indépendantes facilitent souvent la vectorisation.

Garder un accumulateur dans un registre évite des accès mémoire répétés. Mais multiplier les accumulateurs ou dérouler fortement les boucles peut épuiser les registres, provoquer des *spills* et augmenter la taille du code. Ces effets doivent être mesurés.

### Gains possibles et contreparties

| Optimisation | Pourquoi elle peut aider | Compromis à vérifier |
| --- | --- | --- |
| Meilleur algorithme | Réduire le travail nécessaire. | Coûts fixes, taille utile, précision et accès mémoire. |
| Stockage dense et accès contigus | Exploiter les lignes de cache, limiter les indirections. | Réorganisation ou conversion nécessaire. |
| Réutilisation d'une valeur ou d'un bloc | Réduire les rechargements. | Capacité de cache et de registres. |
| Éviter copies et allocations répétées | Réduire les transferts et frais de préparation. | Données à conserver ou à réinitialiser. |
| Calcul par blocs, *tiling* | Réutiliser un ensemble de données proche des unités de calcul. | Taille de bloc, bords et gestion des boucles. |
| Transposition ou *packing* | Rendre des accès plus réguliers ou contigus. | Coût initial, mémoire supplémentaire et amortissement. |
| Bibliothèque BLAS | Utiliser des noyaux adaptés au matériel. | Dimensions, précision, stockage et nombre de threads. |
| Parallélisation | Distribuer du travail indépendant. | Coordination, partage mémoire et consommation. |
| Précision réduite si autorisée | Réduire le volume des données et parfois accélérer le calcul. | Erreur numérique et capacités du matériel. |

**Ne pas tout modifier simultanément :** une transformation à la fois permet d'en expliquer le gain. Cette liste regroupe le cours et des prolongements pratiques ; elle ne constitue pas une liste d'exercices obligatoires. *(Cours, p. 39 et 44-52 ; compléments sur SIMD et registres.)*

## 10. Application : multiplication de matrices

Pour A de dimension M × K et B de dimension K × N :

```text
C[i,j] = somme sur k de A[i,k] × B[k,j]
Coût classique : Θ(MNK), soit Θ(N³) pour des matrices carrées.
Travail conventionnel : environ 2MNK opérations flottantes.
```

Doubler N multiplie approximativement le travail arithmétique par huit et le stockage des matrices par quatre.

### Réordonner les boucles

Dans l'ordre `i-j-k`, A est parcourue par lignes mais B par colonnes si les deux sont stockées par lignes.

L'ordre `i-k-j` rend les accès à B et C contigus dans la boucle interne :

```text
mettre C à zéro
pour i :
    pour k :
        aik = A[i,k]
        pour j :
            C[i,j] += aik × B[k,j]
```

Cette version réutilise aussi `aik`. La complexité reste Θ(MNK) : le gain provient du comportement mémoire et de l'exécution. La remise à zéro de C est indispensable pour cette formulation par accumulation.

### Transposer ou réorganiser

Construire BT tel que `BT[j,k] = B[k,j]` permet de lire deux lignes dans le produit scalaire `A[i,k] × BT[j,k]`. Comparer **produit seul** et **préparation + produit**, puis considérer le nombre de réutilisations de B. Une vue transposée ne garantit pas la nouvelle disposition physique recherchée.

### Calculer par blocs

On calcule des sous-matrices et les réutilise avant de passer aux suivantes. Pour trois blocs carrés de côté b en 64 bits, leurs données occupent environ `3 × b² × 8` octets : **24 KiB pour b = 32**.

Ce calcul aide à raisonner ; il ne garantit pas un usage optimal du cache. Un bloc trop petit ajoute de la gestion, un bloc trop grand perd de la réutilisation. Il faut gérer les dimensions non multiples du bloc et mesurer plusieurs tailles. Une bibliothèque peut bloquer à plusieurs niveaux, jusqu'aux registres.

**À comparer :** version naïve, boucles réordonnées, transposition, blocs et BLAS, sur les mêmes données et à la même précision. *(Cours, p. 46-52 ; développements pratiques.)*

## 11. Multicœur : pourquoi davantage de threads ne suffit pas

```text
Accélération S(p) = T(1) / T(p), pour le même problème avec p threads.
Efficacité parallèle = S(p) / p.
```

Créer et coordonner des threads coûte du temps. Des tâches trop petites peuvent perdre le bénéfice du parallélisme. Le nombre de cœurs physiques, les fréquences et les ressources partagées comptent.

Points à surveiller :

- **Courses d'écriture** : plusieurs threads ne doivent pas modifier sans coordination le même résultat. Distribuer des lignes ou blocs distincts de C simplifie le produit matriciel.
- **Réductions** : une somme distribuée nécessite une combinaison correcte des résultats partiels ; changer l'ordre peut changer les arrondis.
- **Bande passante** : si la RAM est déjà saturée, ajouter des cœurs peut apporter peu de gain.
- **False sharing, complément** : des threads écrivant des variables distinctes sur une même ligne de cache peuvent déclencher des échanges de cohérence. Une indépendance logique ne garantit pas une indépendance au niveau du cache.
- **Placement** : partage des L3 et proximité des données. Sur une machine NUMA, la mémoire locale à un processeur peut être plus favorable qu'une mémoire distante.
- **Surabonnement** : une zone OpenMP appelant une BLAS multithread peut lancer trop de threads.
- **Thermique** : charger plus de cœurs peut réduire leur fréquence et augmenter la puissance.

**Choisir le nombre de threads par mesure**, en distinguant meilleur temps et meilleure énergie. Les précisions de cohérence et de NUMA prolongent les schémas du cours et dépendent du matériel. *(Cours, p. 25, 34 et 49-52.)*

## 12. CPU ou GPU : comment décider ?

| CPU | GPU |
| --- | --- |
| Adapté au contrôle, aux tâches variées et à de nombreuses dépendances. | Adapté à beaucoup d'opérations parallèles suffisamment régulières. |
| Souvent intéressant pour un petit calcul ou des données déjà accessibles au CPU. | Peut être très efficace pour de gros calculs denses et des données réutilisées sur le GPU. |
| Ses cœurs partagent la RAM du système. | Un GPU dédié a généralement une mémoire propre ; il faut compter les transferts. |
| Quelques threads peuvent suffire selon la tâche. | Il faut assez de travail pour occuper les unités et amortir le lancement. |

Les « cœurs » CPU et GPU désignent des organisations différentes : leurs nombres ne permettent pas une comparaison directe.

Pour un GPU dédié, le coût complet comprend notamment :

```text
Préparation + transfert CPU→GPU + lancement/calcul GPU + transfert GPU→CPU
```

Un noyau rapide ne suffit pas si les transferts dominent. Garder les données sur le GPU entre opérations peut changer le bilan. Les systèmes à mémoire partagée ou unifiée ont d'autres chemins et coûts : une adresse accessible ne signifie pas un accès gratuit.

*(Cours, p. 14, 39 et 52 ; complément : [NVIDIA, échanges entre hôte et accélérateur](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html#data-transfer-between-host-and-device).)*

## 13. Mémoires et optimisations GPU à connaître

**Complément pour la suite :** le PDF annonce le GPU sans développer ces mécanismes. La terminologie suit un modèle CUDA ; l'organisation exacte varie entre GPU.

| Ressource | Utilisation et compromis |
| --- | --- |
| Mémoire globale / VRAM | Grande mémoire de travail du GPU ; accès coûteux malgré un débit élevé. |
| Caches L2 et L1 selon l'architecture | Réutilisation automatique ; organisation distincte de celle du CPU. |
| Shared memory | Mémoire rapide sur la puce utilisée explicitement par un groupe de threads ; capacité limitée. |
| Registres | Valeurs de chaque thread ; leur consommation peut limiter les groupes actifs ou provoquer des débordements. |

La **shared memory GPU** n'est pas simplement la RAM partagée entre cœurs CPU. Elle permet notamment de charger et réutiliser un bloc entre threads.

Leviers principaux :

- Réduire les transferts et garder les résultats intermédiaires sur GPU.
- **Coalescing** : faire accéder des threads voisins à des adresses voisines pour regrouper les transactions.
- Réutiliser les blocs en shared memory, en comptant les synchronisations.
- Éviter les **conflits de banques**, qui peuvent sérialiser des accès à cette mémoire.
- Ajuster les blocs : registres, shared memory et threads limitent le nombre de blocs simultanés.
- Limiter les chemins d'exécution divergents entre threads d'un même groupe.
- Chevaucher transferts et calculs lorsque le matériel et les dépendances le permettent.

Dans le modèle CUDA, un **warp** est un groupe de 32 threads exécutant un même flux d'instructions avec un mécanisme de gestion des divergences. L'**occupancy** est le rapport entre le nombre de warps actifs sur un multiprocesseur et le maximum possible. La maximiser ne garantit pas le meilleur temps.

Sources : [NVIDIA, optimisation mémoire](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html#memory-optimizations) et [occupancy](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html#occupancy).

## 14. Mesurer correctement avant de conclure

### Temps et correction

- Comparer le même problème, les mêmes données et une précision comparable ; vérifier les résultats.
- Séparer compilation JIT et démarrage du régime établi.
- Annoncer si copies, transpositions, allocations et transferts sont inclus.
- Relever les threads et bibliothèques réellement utilisés.
- Répéter les mesures et conserver leur dispersion.
- Sur GPU, chronométrer un calcul **effectivement terminé** : un lancement peut être asynchrone. Employer une synchronisation adaptée ou des événements GPU. Voir [NVIDIA, chronométrage](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html#timing).

### Puissance et énergie

```text
Puissance P : watts, avec 1 W = 1 J/s.
Énergie totale : intégrale de P_charge(t) sur la durée.
Avec la puissance moyenne : E_total = P_moyenne × T.
Énergie supplémentaire : intégrale de [P_charge(t) - P_repos] sur la durée.
À référence stable : E_supplémentaire ≈ ΔP_moyenne × T.
```

La consommation de base ne disparaît pas lorsqu'on la soustrait pour étudier le surcoût d'une tâche : il faut l'attribuer dans un bilan complet.

Une machine froide peut bénéficier d'une fréquence temporairement élevée. Sous charge prolongée, refroidissement et limites électriques influencent la fréquence stable. Comparer des états thermiques comparables. **Machine chaude et caches remplis sont deux notions différentes.**

Augmenter la fréquence peut réduire le temps mais augmenter la puissance : le minimum d'énergie peut être intermédiaire. Même logique pour le nombre de threads. « Low power » et « plus rapide » ne garantissent pas « moins de joules ».

Préciser le capteur : CPU, GPU ou machine entière. Sans capteur exploitable, annoncer l'absence de mesure d'énergie ; le TDP n'est pas une mesure du calcul exécuté. *(Cours, p. 28-33.)*

## 15. Contexte environnemental à conserver

- Le bilan inclut matières premières, fabrication, usage et fin de vie. Prolonger la durée de vie du matériel est souvent bénéfique.
- Le CO₂ ne résume pas les impacts : eau, toxicité, ressources et déchets comptent aussi.
- L'efficacité des centres de données ne suffit pas : terminaux et réseaux contribuent au bilan.
- Le refroidissement intervient du processeur au centre de données ; son énergie doit être comptée dans le périmètre choisi.
- **TOP500** : performance mesurée. **Green500** : performance par watt, équivalente aux opérations par joule. Une bonne efficacité n'implique pas une faible consommation totale.
- **Effet rebond** : économiser par opération peut être annulé par davantage d'opérations.
- **ICT / TIC** : technologies de l'information et de la communication, comprenant terminaux, réseaux et centres de données.

*(Cours, p. 4-18 et 35-40.)*

## 16. Quelle optimisation essayer ensuite ?

| Observation | Piste à examiner | Vérification |
| --- | --- | --- |
| Nombreuses petites opérations en boucles Python | Bibliothèque native ou JIT. | Types, correction et coût initial. |
| Parcours de matrice lent | Ordre des boucles et strides. | Stockage réel et dépendances. |
| Données souvent rechargées | Blocs, réutilisation et réduction des temporaires. | Ensemble de travail et préparation. |
| Peu de gain avec plus de cœurs | Bande passante, synchronisation et nombre de threads. | Ressource réellement saturée. |
| Noyau GPU rapide mais opération complète lente | Transferts et maintien des données sur GPU. | Mesure de bout en bout. |
| Peu de gain malgré les caches | Dépendances, instructions ou vectorisation. | Profilage plutôt qu'une seule hypothèse. |
| Version rapide mais énergivore | Fréquence, puissance et nombre de threads. | Joules par résultat correct. |

**Pour chaque changement : quel travail ou déplacement de données est supprimé, quel coût est ajouté, et les mesures confirment-elles le gain ?**

